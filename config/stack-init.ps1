#Requires -Version 5.1
<#
=============================================================================
  Claude Code Context Stack  -  global installer + per-repo init  (Windows)
=============================================================================

  WHAT THIS IS
  Four tools that cut the token cost of working in a real codebase with Claude
  Code, plus the routing rules that make Claude actually use them. Nothing else
  - no spec/ADR/worklog layer. Each tool kills one source of wasted context:

    graphify  structure   one-time codebase graph (tree-sitter, local).
                          Kills ORIENTATION cost - "what connects X to Y /
                          blast radius / how is this organized" with no file
                          spelunking.
    Serena    symbols     LSP over MCP (rust-analyzer / tsserver / pyright).
                          Kills RETRIEVAL+EDIT cost - exact defs, refs,
                          implementations, diagnostics, symbol-level edits.
    RTK       output      Bash PreToolUse hook compressing command output
                          60-90% before it hits the window. Invisible.
    Headroom  wire        Local proxy (`headroom wrap claude`) that recompresses
                          whatever still reaches the API after the three layers
                          above - file dumps, growing history. Second pass, not
                          a replacement for any of them.

  PRINCIPLE: one question per layer.
    architecture/cross-module -> graphify  |  specific symbols -> Serena
    compile/type diagnostics  -> Serena    |  execute anything  -> Bash (RTK)
    everything left over at the wire -> Headroom (catch-all, not a router)
  PRECEDENCE on conflict: LSP (Serena, live) > graph (can be stale).

  GLOBAL vs PER-REPO
    Global (once): RTK hook, Serena at user scope + serena-autoinit SessionStart
      hook (Serena does NOT activate from cwd on its own - it needs a
      .serena\project.yml, which that hook writes per checkout),
      graphify install + graph-autobuild SessionStart hook, Headroom install +
      claude shim, routing contract in $env:USERPROFILE\.claude\CLAUDE.md.
    Per-repo: nothing required - the first session inside any git repo builds
      its graph in the background. `init` remains for building one eagerly (and
      for the tracked-file extras autobuild never touches: .gitignore,
      .claude\agents contract injection).

  USAGE
    .\stack-init.ps1            # or: global   -> global install (once)
    .\stack-init.ps1 init       # inside a repo -> build graph + hooks eagerly
    .\stack-init.ps1 verify     # check wiring
    .\stack-init.ps1 contract   # print the routing contract
    .\stack-init.ps1 contract --condensed  # print the short form injected into agents
    .\stack-init.ps1 stats      # append + print a usage snapshot (rtk/headroom)

  AFTER GLOBAL INSTALL: open a NEW terminal. Bare `claude` then launches through
  Headroom automatically via a shim (CLAUDE_NO_HEADROOM=1 bypasses it for one
  run), and the first session in any git repo autobuilds its graph in the
  background (opt out: CLAUDE_STACK_NO_AUTOBUILD=1, or a .graphify-skip file in
  the repo root).

  PREREQS: cargo, pip, uv, claude (Claude Code CLI), Git for Windows (its bash
  runs the post-commit hook). A language server per language. First run may need
  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned (or -ExecutionPolicy Bypass).
=============================================================================
#>
param([string]$Command = 'global', [string]$SubOption = '')
$ErrorActionPreference = 'Stop'

$ClaudeDir = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE '.claude' }
$ClaudeMd  = Join-Path $ClaudeDir 'CLAUDE.md'
function Say ($m){ Write-Host "==> "   -ForegroundColor Green  -NoNewline; Write-Host $m }
function Warn($m){ Write-Host "warn: " -ForegroundColor Yellow -NoNewline; Write-Host $m }
function Err ($m){ Write-Host "error: "-ForegroundColor Red    -NoNewline; Write-Host $m }
function Have($c){ [bool](Get-Command $c -ErrorAction SilentlyContinue) }

$Contract = @'
# >>> claude-context-stack >>> (managed by stack-init - edits here are overwritten)
## Context routing (non-negotiable)
1. Architecture / cross-module / "what connects X to Y" / blast radius:
   IF graphify-out/ exists -> read graphify-out/GRAPH_REPORT.md or run
   `graphify query "..."` / `graphify path A B`. Never orient by reading files or grep.
   IF absent -> orient normally (the stack autobuilds the graph in the background
   at session start - it may simply not be ready yet).
2. Specific symbols (definitions, references, implementations, file overviews)
   -> Serena (find_symbol, find_referencing_symbols, get_symbols_overview).
   Never grep for symbol names.
3. Compile / type / lint state -> Serena get_diagnostics_for_file.
   Do not run a full type-check just to read diagnostics Serena already provides.
4. Edits to existing symbols -> Serena symbol-level edits (replace_symbol_body,
   insert_after_symbol, rename_symbol), not string/regex replacement.
5. Anything that executes (tests, builds, git, tooling) -> Bash. RTK compresses it.
   Do NOT route execution through an MCP shell tool or the PowerShell tool -
   RTK's hook matches Bash only, so both hand back uncompressed output.
   PowerShell is for genuinely Windows-only work (registry, COM, cmdlets).
6. The graph reflects the last REBUILD (normally the last commit).
   - Symbol-level questions about uncommitted work -> Serena (live). Never the graph.
   - ARCHITECTURAL questions that involve uncommitted work -> run `graphify update .`
     first (incremental, content-hash cached, cheap), then query the graph as normal.

## Source-of-truth precedence (on conflict)
code/LSP (Serena)  >  graph (graphify)
The LSP is live ground truth; the graph is a derivation that can trail the working
tree. On conflict, trust the LSP and rebuild the graph (`graphify update .`).
# <<< claude-context-stack <<<
'@

$ContractCondensed = @'
# >>> claude-context-stack >>> (condensed, managed by stack-init - edits here are overwritten)
1. Architecture/cross-module -> graphify (graphify-out/GRAPH_REPORT.md, `graphify query`/`path`). Never grep/read-many for this.
2. Specific symbols -> Serena (find_symbol, find_referencing_symbols, get_symbols_overview). Never grep for symbol names.
5. Anything that executes -> Bash (RTK compresses it). Never an MCP shell tool, and on Windows never the PowerShell tool either (RTK's hook is Bash-only) except for Windows-only work.
6. Graph = last REBUILD. Uncommitted+symbol -> Serena. Uncommitted+architectural -> `graphify update .` first, then query.
Precedence on conflict: code/LSP (Serena) > graph (graphify).
# <<< claude-context-stack <<<
'@

# Skills for the extras (opensrc, worktrunk). graphify deploys its own via
# `graphify install`; these two ship none, and without a SKILL.md in
# $ClaudeDir\skills Claude has the binaries on PATH but nothing ever surfaces
# them - the skill description is what makes the agent reach for the tool.
# Canonical copies live in skills/<name>/ in the agent-skills repo (SKILL.md
# plus any supporting files), where they work as ordinary standalone Claude
# skills; this script only DEPLOYS them, verbatim (no stack-specific text
# appended - the skills already carry their Context Stack interop notes).
# Source: the repo checkout next to this script - the script ships inside the
# repo, so run it from there (no network fallback by design). Non-fatal like
# the extras themselves.
function Install-ExtraSkill {
  param([string]$Name)
  $src = Join-Path $PSScriptRoot "..\skills\$Name"
  if (-not (Test-Path (Join-Path $src 'SKILL.md'))) {
    Warn "$Name skill not deployed - skills\$Name\SKILL.md not found next to this script; run stack-init from the agent-skills repo checkout"
    return
  }
  $dst = Join-Path $ClaudeDir "skills\$Name"
  # Mirror the whole skill directory, not just SKILL.md - skills may ship
  # supporting files (references/, scripts/, ...). Delete-then-copy so files
  # removed from the repo don't linger: the deployed copy is fully managed by
  # this step, never hand-edited.
  if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }
  New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
  Copy-Item -Recurse -Force $src $dst
  Say "  $Name skill deployed (from repo skills\)"
}

function Invoke-InjectCondensedContract {
  param([string]$Dir)
  if (-not (Test-Path $Dir -PathType Container)) {
    Say "  no agent files at $Dir - skipping condensed contract injection"
    return
  }
  $files = Get-ChildItem -Path $Dir -Filter '*.md' -File -ErrorAction SilentlyContinue
  if (-not $files) {
    Say "  no agent files at $Dir - skipping condensed contract injection"
    return
  }
  foreach ($f in $files) {
    $existing = Get-Content -Raw $f.FullName
    $stripped = [regex]::Replace($existing,
      '(?s)# >>> claude-context-stack >>>.*?# <<< claude-context-stack <<<\r?\n?', '')
    $out = ($stripped.TrimEnd() + "`r`n`r`n" + $ContractCondensed).TrimStart()
    Set-Content -Path $f.FullName -Value $out -Encoding utf8
  }
  Say "  condensed contract injected into $Dir\*.md"
}

function Check-Deps {
  $miss = $false
  foreach ($d in 'git','claude') { if (-not (Have $d)) { Err "missing required: $d"; $miss = $true } }
  if (-not (Have 'cargo')) { Warn "cargo not found - needed to install RTK" }
  if (-not (Have 'pip'))   { Warn "pip not found - needed to install graphify" }
  if ($miss) { Err "install the required tools above, then re-run"; exit 1 }
}

function Write-GitHook {
  # Merge-not-clobber: skip if our marker is already there, append under the
  # marker if some other tool owns the file, otherwise create it fresh. Hook
  # bodies are POSIX sh - Git for Windows runs hooks via its bundled bash
  # regardless of host OS, same as the existing post-commit hook.
  param([string]$Name, [string]$Body)
  # [IO.File] resolves relative paths against .NET's process-wide current
  # directory, which does NOT track PowerShell's Set-Location/Push-Location -
  # always resolve to an absolute path via $PWD first, or this can write into
  # whatever directory the process originally launched from instead of cwd.
  $path = Join-Path (Join-Path $PWD.Path '.git\hooks') $Name
  if ((Test-Path $path) -and (Select-String -Path $path -Pattern 'claude-context-stack:' -Quiet)) { return }
  if (Test-Path $path) {
    [IO.File]::AppendAllText($path, "`n$Body`n")
  } else {
    [IO.File]::WriteAllText($path, "#!/bin/sh`n$Body`n")
  }
}

function Install-RefreshHooks {
  Write-GitHook 'post-checkout' @'
# claude-context-stack: refresh graph on branch switch (not file checkout)
if [ "$3" = "1" ] && command -v graphify >/dev/null 2>&1 && [ -d graphify-out ]; then
  ( graphify update . >/dev/null 2>&1 & )
fi
'@
  Write-GitHook 'post-merge' @'
# claude-context-stack: refresh graph after merge/pull
command -v graphify >/dev/null 2>&1 && [ -d graphify-out ] && graphify update . >/dev/null 2>&1 || true
'@
  Write-GitHook 'post-rewrite' @'
# claude-context-stack: refresh graph after rebase
command -v graphify >/dev/null 2>&1 && [ -d graphify-out ] && graphify update . >/dev/null 2>&1 || true
'@
}

function Install-Uv {
  if (Have 'uv') { return }
  Say "  installing uv (needed to run Serena)"
  if (Have 'winget') { winget install --id astral-sh.uv -e --silent }
  else { powershell -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex" }
  if (-not (Have 'uv')) { Warn "uv install failed - Serena will not be able to launch" }
}

function Register-SessionStartHook {
  # Adds a SessionStart command hook to global settings.json (idempotent) and
  # returns the parsed settings object so callers can inspect other hooks.
  param([string]$Cmd)
  $settingsPath = Join-Path $ClaudeDir 'settings.json'
  $json = if (Test-Path $settingsPath) { Get-Content -Raw $settingsPath } else { '{}' }
  try { $data = $json | ConvertFrom-Json } catch { $data = [PSCustomObject]@{} }
  if (-not $data.PSObject.Properties['hooks']) { $data | Add-Member -NotePropertyName hooks -NotePropertyValue ([PSCustomObject]@{}) }
  if (-not $data.hooks.PSObject.Properties['SessionStart']) { $data.hooks | Add-Member -NotePropertyName SessionStart -NotePropertyValue @() }
  $starts = @($data.hooks.SessionStart)
  $already = $starts | Where-Object { $_.hooks | Where-Object { $_.command -eq $Cmd } }
  if (-not $already) {
    $starts += [PSCustomObject]@{ hooks = @([PSCustomObject]@{ type = 'command'; command = $Cmd }) }
    $data.hooks.SessionStart = $starts
  }
  New-Item -ItemType Directory -Force -Path $ClaudeDir | Out-Null
  $data | ConvertTo-Json -Depth 20 | Set-Content -Path $settingsPath -Encoding utf8
  return $data
}

function Set-GlobalEnvVar {
  # Writes settings.json env.<Name> unless the user already set it (their value
  # wins - this is a floor, not a policy).
  param([string]$Name, [string]$Value)
  $settingsPath = Join-Path $ClaudeDir 'settings.json'
  $json = if (Test-Path $settingsPath) { Get-Content -Raw $settingsPath } else { '{}' }
  try { $data = $json | ConvertFrom-Json } catch { $data = [PSCustomObject]@{} }
  if (-not $data.PSObject.Properties['env']) { $data | Add-Member -NotePropertyName env -NotePropertyValue ([PSCustomObject]@{}) }
  if ($data.env.PSObject.Properties[$Name]) {
    Say "  settings.json env.$Name already set ($($data.env.$Name)) - left alone"
    return
  }
  $data.env | Add-Member -NotePropertyName $Name -NotePropertyValue $Value
  New-Item -ItemType Directory -Force -Path $ClaudeDir | Out-Null
  $data | ConvertTo-Json -Depth 20 | Set-Content -Path $settingsPath -Encoding utf8
  Say "  settings.json env.$Name = $Value"
}

function Install-HeadroomCheck {
  $hooksDir = Join-Path $ClaudeDir 'hooks'
  New-Item -ItemType Directory -Force -Path $hooksDir | Out-Null
  $checkPath = Join-Path $hooksDir 'headroom-check.ps1'
  Set-Content -Path $checkPath -Encoding utf8 -Value @'
$url = $env:ANTHROPIC_BASE_URL
if ($url -match "127\.0\.0\.1|localhost") { exit 0 }
$note = "NOTE: Headroom proxy not active this session (bare launch). Wire-level compression off; RTK/Serena/graphify unaffected."
@{ hookSpecificOutput = @{ hookEventName = "SessionStart"; additionalContext = $note } } | ConvertTo-Json -Compress
exit 0
'@

  $cmd = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$checkPath`""
  $data = Register-SessionStartHook $cmd
  $rtkPresent = $false
  if ($data.hooks.PSObject.Properties['PreToolUse']) {
    $rtkPresent = (($data.hooks.PreToolUse | ConvertTo-Json -Depth 10) -match 'rtk')
  }
  if ($rtkPresent) { Say "  SessionStart headroom-check hook installed; RTK PreToolUse hook still present" }
  else { Warn "settings.json written but RTK's Bash hook wasn't found afterward - check settings.json manually" }
}

function Install-GraphAutobuild {
  # Replaces per-repo `init` for the common case: a SessionStart hook that, in
  # any git repo, builds a missing graph in the background and refreshes an
  # existing one (incremental, content-hash cached). All side effects stay
  # under .git/ (hooks, info/exclude, lock) - it never mutates tracked files,
  # which is why it writes .git/info/exclude rather than .gitignore and does
  # NOT inject the condensed contract into repo .claude\agents\. Run `init`
  # for the eager/tracked-file variant.
  $hooksDir = Join-Path $ClaudeDir 'hooks'
  New-Item -ItemType Directory -Force -Path $hooksDir | Out-Null
  $autoPath = Join-Path $hooksDir 'graph-autobuild.ps1'
  Set-Content -Path $autoPath -Encoding utf8 -Value @'
param([switch]$Build)
# claude-context-stack: per-repo graph autobuild/refresh at session start.
# Opt out: CLAUDE_STACK_NO_AUTOBUILD=1, or a .graphify-skip file in the repo
# root. Remove the SessionStart entry in settings.json to uninstall.
$ErrorActionPreference = 'SilentlyContinue'

$top = git rev-parse --show-toplevel 2>$null
if (-not $top -or -not (Test-Path $top)) { exit 0 }
Set-Location $top
$gd  = git rev-parse --git-dir 2>$null
if (-not $gd) { exit 0 }
if (-not [IO.Path]::IsPathRooted($gd)) { $gd = Join-Path $top $gd }
$cgd = git rev-parse --git-common-dir 2>$null
if (-not $cgd) { $cgd = $gd }
elseif (-not [IO.Path]::IsPathRooted($cgd)) { $cgd = Join-Path $top $cgd }
$lock = Join-Path $gd 'claude-stack-autobuild.lock'

# Points graphify's post-commit hook at an interpreter that can actually import
# graphify, by writing the override file the hook reads when its baked-in pin is
# dead. Forward slashes are required, not cosmetic: the hook allowlists the file
# contents against [a-zA-Z0-9/_.@:-], so a backslashed Windows path is discarded.
function Repair-GraphifyPython {
  $pin = Join-Path $top 'graphify-out\.graphify_python'
  if (Test-Path $pin) {
    $raw = Get-Content -Raw $pin -ErrorAction SilentlyContinue
    if ($raw) {
      $cur = $raw.Trim()
      if ($cur -and (Test-Path $cur)) { return }
    }
  }
  # uv colourises even when redirected, and an ESC[36m prefix turns the drive
  # letter into a bogus PowerShell drive - strip SGR sequences before use.
  $ud = (uv tool dir 2>$null | Out-String) -replace "$([char]27)\[[0-9;]*m", ''
  $ud = $ud.Trim()
  if (-not $ud) { return }
  foreach ($rel in @('graphifyy\Scripts\python.exe', 'graphifyy\bin\python')) {
    $cand = Join-Path $ud $rel
    if (-not (Test-Path $cand)) { continue }
    & $cand -c 'import graphify' *> $null
    if ($LASTEXITCODE -ne 0) { continue }
    New-Item -ItemType Directory -Force -Path (Split-Path $pin) | Out-Null
    Set-Content -Path $pin -Value ($cand -replace '\\','/') -Encoding ascii -NoNewline
    return
  }
}

# Repo-local git hooks that keep the graph fresh. Idempotent, and deliberately
# NOT confined to the first build: a repo whose graph predates this logic hits
# the fast path below and returns early, so it would never acquire the refresh
# hooks and would keep a stale post-commit pin forever.
function Ensure-RepoHooks ($cgd) {
  $hooksDir = Join-Path $cgd 'hooks'
  New-Item -ItemType Directory -Force -Path $hooksDir | Out-Null
  $nl = "`n"
  # post-commit is graphify's own hook. Install it when absent. When it exists
  # but the interpreter it pinned at install time has gone away (interpreter
  # uninstalled, pip -> uv tool migration), a plain re-install is NOT a repair:
  # graphify matches its own marker, reports "already installed" and leaves the
  # dead pin, so every commit silently fails to rebuild the graph. `hook
  # uninstall` + `hook install` does re-pin, but uninstall deletes .gitattributes
  # when the merge driver is its only entry - too destructive to run unattended
  # at session start. Repair through graphify's documented second detection
  # path instead: graphify-out/.graphify_python, additive and inside the
  # already-ignored output dir.
  $pc = Join-Path $hooksDir 'post-commit'
  if (-not (Test-Path $pc)) { graphify hook install *> $null }
  else {
    $txt = Get-Content -Raw $pc
    if ($txt -notmatch 'graphify-hook-start') { graphify hook install *> $null }
    elseif (($txt -match "_PINNED='([^']+)'") -and -not (Test-Path $matches[1])) { Repair-GraphifyPython }
  }
  $bodies = @{
    'post-checkout' = ('# claude-context-stack: refresh graph on branch switch (not file checkout)' + $nl +
      'if [ "$3" = "1" ] && command -v graphify >/dev/null 2>&1 && [ -d graphify-out ]; then' + $nl +
      '  ( graphify update . >/dev/null 2>&1 & )' + $nl + 'fi')
    'post-merge'    = ('# claude-context-stack: refresh graph after merge/pull' + $nl +
      'command -v graphify >/dev/null 2>&1 && [ -d graphify-out ] && graphify update . >/dev/null 2>&1 || true')
    'post-rewrite'  = ('# claude-context-stack: refresh graph after rebase' + $nl +
      'command -v graphify >/dev/null 2>&1 && [ -d graphify-out ] && graphify update . >/dev/null 2>&1 || true')
  }
  foreach ($name in @($bodies.Keys)) {
    $p = Join-Path $hooksDir $name
    if ((Test-Path $p) -and (Select-String -Path $p -Pattern 'claude-context-stack:' -Quiet)) { continue }
    if (Test-Path $p) { [IO.File]::AppendAllText($p, $nl + $bodies[$name] + $nl) }
    else { [IO.File]::WriteAllText($p, '#!/bin/sh' + $nl + $bodies[$name] + $nl) }
  }
}

if ($Build) {
  # Background worker: the actual first build. Everything it writes lives
  # under .git/ - never a tracked file (no .gitignore, no .claude/agents).
  try {
    graphify . *> $null
    Ensure-RepoHooks $cgd
    $info = Join-Path $cgd 'info'
    New-Item -ItemType Directory -Force -Path $info | Out-Null
    $excl = Join-Path $info 'exclude'
    $cur = if (Test-Path $excl) { Get-Content -Raw $excl } else { '' }
    if ($cur -notmatch '(?m)^graphify-out/') { [IO.File]::AppendAllText($excl, $nl + 'graphify-out/' + $nl) }
  } finally { Remove-Item -Recurse -Force $lock }
  exit 0
}

if ($env:CLAUDE_STACK_NO_AUTOBUILD) { exit 0 }
if (Test-Path (Join-Path $top '.graphify-skip')) { exit 0 }
if (-not (Get-Command graphify -ErrorAction SilentlyContinue)) { exit 0 }

if (Test-Path (Join-Path $top 'graphify-out')) {
  # Backfill for repos whose graph predates this hook logic, and self-heal for a
  # dead post-commit pin. Both checks are file tests that no-op once satisfied.
  Ensure-RepoHooks $cgd
  Start-Process -WindowStyle Hidden -FilePath graphify -ArgumentList 'update','.' -WorkingDirectory $top | Out-Null
  exit 0
}

try { New-Item -ItemType Directory -Path $lock -ErrorAction Stop | Out-Null }
catch {
  $item = Get-Item $lock -ErrorAction SilentlyContinue
  if ($item -and ((Get-Date) - $item.CreationTime).TotalMinutes -lt 60) { exit 0 }
  Remove-Item -Recurse -Force $lock -ErrorAction SilentlyContinue
  try { New-Item -ItemType Directory -Path $lock -ErrorAction Stop | Out-Null } catch { exit 0 }
}
Start-Process -WindowStyle Hidden -FilePath powershell -ArgumentList @(
  '-NoProfile','-ExecutionPolicy','Bypass','-File',$PSCommandPath,'-Build') -WorkingDirectory $top | Out-Null
@{ hookSpecificOutput = @{ hookEventName = 'SessionStart'; additionalContext =
  'graphify: no graph in this repo yet - the stack is building one in the background (first build can take a while on big repos). Orient normally until graphify-out/ appears; do not run graphify . yourself.' } } | ConvertTo-Json -Compress
exit 0
'@

  Register-SessionStartHook "powershell -NoProfile -ExecutionPolicy Bypass -File `"$autoPath`"" | Out-Null
  Say "  SessionStart graph-autobuild hook installed (opt out: CLAUDE_STACK_NO_AUTOBUILD=1 or .graphify-skip)"
}

function Install-SerenaAutoInit {
  # Serena does NOT auto-activate from cwd - the claim this installer shipped
  # with was wrong. With no .serena\project.yml it starts with NO active
  # project and every symbol tool fails with "No active project", which is
  # silent: the model just falls back to grep, breaking contract rule 2 with
  # nothing in the UI to say so (the same failure mode as a timed-out MCP
  # launch). Serena's own detection is also too weak to rely on - on a repo of
  # 21 markdown + 1 shell + 1 powershell file it selected powershell alone, so
  # every other file answered "path is ignored". Languages are derived from
  # tracked files here instead.
  $hooksDir = Join-Path $ClaudeDir 'hooks'
  New-Item -ItemType Directory -Force -Path $hooksDir | Out-Null
  $serenaPath = Join-Path $hooksDir 'serena-autoinit.ps1'
  Set-Content -Path $serenaPath -Encoding utf8 -Value @'
# claude-context-stack: per-checkout Serena project init at session start.
# Opt out: CLAUDE_STACK_NO_SERENA_INIT=1, or a .serena-skip file in the root.
# Uninstall: remove the SessionStart entry in settings.json.
$ErrorActionPreference = 'SilentlyContinue'

if ($env:CLAUDE_STACK_NO_SERENA_INIT) { exit 0 }
if (-not (Get-Command serena -ErrorAction SilentlyContinue)) { exit 0 }
$top = git rev-parse --show-toplevel 2>$null
if (-not $top -or -not (Test-Path $top)) { exit 0 }
Set-Location $top
if (Test-Path '.serena-skip') { exit 0 }
if (Test-Path (Join-Path $top '.serena/project.yml')) { exit 0 }

$gd = git rev-parse --git-dir 2>$null
if (-not $gd) { exit 0 }
if (-not [IO.Path]::IsPathRooted($gd)) { $gd = Join-Path $top $gd }
$cgd = git rev-parse --git-common-dir 2>$null
if (-not $cgd) { $cgd = $gd }
elseif (-not [IO.Path]::IsPathRooted($cgd)) { $cgd = Join-Path $top $cgd }
# GetFullPath, not Resolve-Path: normalises without touching the filesystem, so
# a worktree whose git dir has been pruned still compares cleanly.
$isMain = ([IO.Path]::GetFullPath($gd) -eq [IO.Path]::GetFullPath($cgd))

# Worktrunk: a linked worktree is a separate checkout at its own path, and
# project_serena_folder_location is "$projectDir/.serena", so each worktree
# needs its own project rather than inheriting the main one. serena_config.yml
# keys the registry by path, but names are what activation and the dashboard
# show, so linked worktrees are suffixed with their branch to stay distinct.
$name = Split-Path $top -Leaf
if (-not $isMain) {
  $br = git rev-parse --abbrev-ref HEAD 2>$null
  if ($br -and $br -ne 'HEAD') { $name = "$name@$br" }
}

$exts = @(git ls-files 2>$null |
  ForEach-Object { [IO.Path]::GetExtension($_) } |
  Where-Object { $_ } |
  ForEach-Object { $_.TrimStart('.').ToLower() } |
  Sort-Object -Unique)
if (-not $exts) { exit 0 }

$servers = [System.Collections.Generic.List[string]]::new()
function Add-Srv($s) { if (-not $servers.Contains($s)) { $servers.Add($s) } }
function Test-Ext($list) { foreach ($e in $list) { if ($exts -contains $e) { return $true } } return $false }
# Compiled/checked languages first: the FIRST entry is Serena's default and
# fallback server, so a real language should outrank markdown/yaml here.
if (Test-Ext @('rs'))    { Add-Srv 'rust' }
if (Test-Ext @('py'))    { Add-Srv 'python' }
if (Test-Ext @('ts','tsx','js','jsx','mjs','cjs')) { Add-Srv 'typescript' }
if (Test-Ext @('go'))    { Add-Srv 'go' }
if (Test-Ext @('java'))  { Add-Srv 'java' }
if (Test-Ext @('kt'))    { Add-Srv 'kotlin' }
if (Test-Ext @('cs'))    { Add-Srv 'csharp' }
if (Test-Ext @('c','h','cpp','hpp','cc','hh')) { Add-Srv 'cpp' }
if (Test-Ext @('rb'))    { Add-Srv 'ruby' }
if (Test-Ext @('php'))   { Add-Srv 'php' }
if (Test-Ext @('swift')) { Add-Srv 'swift' }
if (Test-Ext @('scala')) { Add-Srv 'scala' }
if (Test-Ext @('lua'))   { Add-Srv 'lua' }
if (Test-Ext @('zig'))   { Add-Srv 'zig' }
if (Test-Ext @('ex','exs')) { Add-Srv 'elixir' }
if (Test-Ext @('tf'))    { Add-Srv 'terraform' }
if (Test-Ext @('sh','bash')) { Add-Srv 'bash' }
if (Test-Ext @('ps1','psm1','psd1')) { Add-Srv 'powershell' }
if (Test-Ext @('md'))    { Add-Srv 'markdown' }
if (Test-Ext @('yml','yaml')) { Add-Srv 'yaml' }
if (Test-Ext @('toml'))  { Add-Srv 'toml' }
if ($servers.Count -eq 0) { exit 0 }

$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('# Generated by claude-context-stack (serena-autoinit). Safe to edit or')
$lines.Add('# delete: it is only written when absent, never overwritten. Machine-local')
$lines.Add('# overrides belong in project.local.yml, which Serena ignores by default.')
$lines.Add('project_name: "' + $name + '"')
$lines.Add('language_servers:')
foreach ($s in $servers) { $lines.Add("- $s") }
$lines.Add('ignore_all_files_in_gitignore: true')
if ($isMain) {
  # Worktrunk nests linked worktrees at .claude\worktrees\ INSIDE the main
  # checkout, so without this the main project indexes every worktree as well
  # and one symbol lookup returns a near-duplicate hit per branch. Emitted
  # unconditionally: worktrees usually appear after this file is generated,
  # and it is inert when the directory does not exist.
  $lines.Add('ignored_paths:')
  $lines.Add('- ".claude/worktrees"')
}
New-Item -ItemType Directory -Force -Path (Join-Path $top '.serena') | Out-Null
# WriteAllText with an explicit no-BOM encoder rather than Set-Content: this
# hook is registered as `powershell -NoProfile ...`, i.e. Windows PowerShell
# 5.1, whose `-Encoding utf8` prepends a BOM. PyYAML and ruamel both strip a
# leading BOM, so it parses either way - but this keeps the file byte-identical
# to the POSIX variant's output instead of depending on that tolerance.
[IO.File]::WriteAllText((Join-Path $top '.serena/project.yml'),
  (($lines -join "`n") + "`n"), (New-Object System.Text.UTF8Encoding $false))

# Keep the generated folder out of git without touching a tracked .gitignore -
# same rule the graph autobuild hook follows. Written to the COMMON git dir so
# one entry covers the main checkout and every worktree hanging off it.
$infoDir = Join-Path $cgd 'info'
New-Item -ItemType Directory -Force -Path $infoDir | Out-Null
$excl = Join-Path $infoDir 'exclude'
if (-not ((Test-Path $excl) -and (Select-String -Path $excl -Pattern '^\.serena/$' -Quiet))) {
  Add-Content -Path $excl -Value "`n.serena/"
}
exit 0
'@

  Register-SessionStartHook "powershell -NoProfile -ExecutionPolicy Bypass -File `"$serenaPath`"" | Out-Null
  Say "  SessionStart serena-autoinit hook installed (opt out: CLAUDE_STACK_NO_SERENA_INIT=1 or .serena-skip)"
}

function Install-ClaudeShim {
  # Shadows bare `claude` so it launches through Headroom automatically. The
  # self-recursion hazard that made shadowing dangerous (headroom re-resolving
  # 'claude' back to the shim - `headroom wrap` only accepts tool names, so
  # re-resolution is unavoidable) is bounded by construction: the shim exports
  # a re-entry guard (CLAUDE_STACK_SHIM) before delegating, so when headroom's
  # PATH search lands back on the shim, that second entry execs the REAL
  # binary (which the shim resolves itself, skipping its own directory) -
  # exactly one bounce, never a loop. An already-wrapped session (localhost
  # ANTHROPIC_BASE_URL) is never double-wrapped. Headroom missing or
  # CLAUDE_NO_HEADROOM=1 falls through to the real binary - a broken shim
  # never blocks a session.
  # $HeadroomFlags carries ' --no-tokensave' when supported: newer headroom
  # builds its own code graph by default, which the stack's decisions log
  # forbids (duplicate of graphify; see the --code-graph entry).
  param([string]$HeadroomFlags = '')
  $binDir = Join-Path $ClaudeDir 'stack-bin'
  New-Item -ItemType Directory -Force -Path $binDir | Out-Null

  $shimPs1 = @'
# claude-context-stack: auto-wrap claude with Headroom (managed by stack-init).
# CLAUDE_NO_HEADROOM=1 skips wrapping for one launch; delete this directory
# (and its PATH entry) to remove the shim entirely.
# `headroom wrap` re-resolves 'claude' on PATH itself and can land back on
# this shim - the CLAUDE_STACK_SHIM guard bounds that to exactly one bounce:
# the re-entered shim execs the real binary directly.
$selfDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$real = Get-Command claude -CommandType Application -All -ErrorAction SilentlyContinue |
  Where-Object { (Split-Path -Parent $_.Source) -ne $selfDir } |
  Select-Object -First 1
if (-not $real) { [Console]::Error.WriteLine('claude shim: real claude binary not found on PATH'); exit 127 }
$bypass = $env:CLAUDE_NO_HEADROOM -or $env:CLAUDE_STACK_SHIM -or
  ($env:ANTHROPIC_BASE_URL -match '127\.0\.0\.1|localhost') -or
  -not (Get-Command headroom -ErrorAction SilentlyContinue)
if ($bypass) { & $real.Source @args; exit $LASTEXITCODE }
$env:CLAUDE_STACK_SHIM = '1'
'@
  $shimPs1 += "`nheadroom wrap claude$HeadroomFlags @args`nexit `$LASTEXITCODE`n"
  Set-Content -Path (Join-Path $binDir 'claude.ps1') -Encoding utf8 -Value $shimPs1

  Set-Content -Path (Join-Path $binDir 'claude.cmd') -Encoding ascii -Value @'
@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0claude.ps1" %*
exit /b %ERRORLEVEL%
'@

  # Git Bash resolves 'claude' by exact name (+.exe), never .cmd - it needs a
  # POSIX shim in the same dir. Must be BOM-less LF or the shebang breaks.
  $shimSh = @'
#!/bin/sh
# claude-context-stack: auto-wrap claude with Headroom (managed by stack-init).
# CLAUDE_NO_HEADROOM=1 skips wrapping for one launch; delete this file (and
# its PATH entry) to remove the shim entirely.
self_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
real=
old_ifs=$IFS
IFS=:
for d in $PATH; do
  [ -n "$d" ] || continue
  [ "$(CDPATH= cd -- "$d" 2>/dev/null && pwd -P)" = "$self_dir" ] && continue
  for n in claude claude.exe claude.cmd; do
    if [ -f "$d/$n" ] && [ -x "$d/$n" ]; then real="$d/$n"; break 2; fi
  done
done
IFS=$old_ifs
if [ -z "$real" ]; then
  echo "claude shim: real claude binary not found on PATH" >&2
  exit 127
fi
wrapped=
case "${ANTHROPIC_BASE_URL:-}" in *127.0.0.1*|*localhost*) wrapped=1 ;; esac
if [ -n "${CLAUDE_NO_HEADROOM:-}" ] || [ -n "${CLAUDE_STACK_SHIM:-}" ] || [ -n "$wrapped" ] \
   || ! command -v headroom >/dev/null 2>&1; then
  exec "$real" "$@"
fi
CLAUDE_STACK_SHIM=1
export CLAUDE_STACK_SHIM
'@
  $shimSh += "`nexec headroom wrap claude$HeadroomFlags `"`$@`""
  [IO.File]::WriteAllText((Join-Path $binDir 'claude'), ($shimSh -replace "`r`n", "`n") + "`n")
  Say "  shim written -> $binDir (claude.cmd / claude.ps1 / claude for Git Bash)"

  # Prepend to user PATH. Raw registry read/write (not [Environment]::Set...)
  # so REG_EXPAND_SZ entries like %USERPROFILE% in the existing PATH survive.
  $rawPath = [string](Get-Item 'HKCU:\Environment').GetValue('Path', '', 'DoNotExpandEnvironmentNames')
  $expanded = [Environment]::ExpandEnvironmentVariables($rawPath)
  if ((';' + $expanded + ';') -notlike "*;$binDir;*") {
    $newPath = if ($rawPath) { "$binDir;$rawPath" } else { $binDir }
    Set-ItemProperty -Path 'HKCU:\Environment' -Name Path -Value $newPath -Type ExpandString
    # Broadcast the change so terminals opened from Explorer see it without a
    # logoff. Best-effort - a failed broadcast just means "new terminal after
    # next logon".
    try {
      Add-Type -Namespace Win32 -Name Native -MemberDefinition '[DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)] public static extern IntPtr SendMessageTimeout(IntPtr hWnd, uint Msg, UIntPtr wParam, string lParam, uint fuFlags, uint uTimeout, out UIntPtr lpdwResult);'
      [UIntPtr]$res = [UIntPtr]::Zero
      [Win32.Native]::SendMessageTimeout([IntPtr]0xffff, 0x1A, [UIntPtr]::Zero, 'Environment', 2, 5000, [ref]$res) | Out-Null
    } catch {}
    Say "  shim dir prepended to user PATH (open a NEW terminal to pick it up)"
  } else {
    Say "  shim dir already on user PATH"
  }
  if ((';' + $env:PATH + ';') -notlike "*;$binDir;*") { $env:PATH = "$binDir;$env:PATH" }
}

function Set-SerenaDashboardConfig {
  # Dashboards stay enabled (one per session, own port each) but no longer
  # auto-open a browser tab per Claude session; the global tray icon
  # (tray_manager) lists every running instance instead. tray_manager is
  # tested on Windows only, which is why the sh installer keeps Serena's
  # stock dashboard behavior.
  $cfg = Join-Path $env:USERPROFILE '.serena\serena_config.yml'
  if (-not (Test-Path $cfg)) {
    Say "  serena_config.yml not found (Serena writes it on first launch) - rerun global later to apply dashboard settings"
    return
  }
  $text = Get-Content $cfg -Raw
  # [^\r\n]* instead of .*$ — in .NET regex `.` matches \r, so .*$ would eat
  # the CR of CRLF files and dirty the diff on every run
  $new = $text -replace '(?m)^web_dashboard_open_on_launch:[^\r\n]*', 'web_dashboard_open_on_launch: false'
  $new = $new -replace '(?m)^web_dashboard_interface:[^\r\n]*', 'web_dashboard_interface: tray_manager'
  if ($new -ne $text) {
    Set-Content -Path $cfg -Encoding utf8 -Value $new
    Say "  serena dashboard: auto-open off; tray_manager icon lists all instances"
  } else {
    Say "  serena dashboard settings already applied"
  }
}

function Install-Global {
  Check-Deps
  Say "RTK - output compression (global Bash hook)"
  if (Have 'rtk') { Say "  rtk present ($(rtk --version 2>$null))" }
  else { Say "  installing rtk"; cargo install --git https://github.com/rtk-ai/rtk }
  rtk init -g; Say "  rtk init -g (PreToolUse Bash hook registered)"

  # One health-check pass, reused by the Serena and Headroom steps below:
  # `claude mcp list` spawns every registered server and waits on it, so
  # calling it twice doubles the slowest step in this function.
  $mcpList = (claude mcp list 2>$null | Out-String)

  Say "Serena - LSP symbols over MCP (user scope, one project per checkout)"
  Install-Uv
  # Serena runs from a uv-installed binary, NOT `uvx --from git+...`: uvx
  # re-resolves the git ref and REBUILDS the package whenever uv's cache is
  # cold, which overruns Claude Code's 30s MCP startup limit and leaves the
  # session with no Serena at all. That failure is silent - the model just
  # falls back to grep, breaking contract rule 2 with nothing in the UI to
  # say so. `uv tool install` pins a built binary, so launch is import-only.
  if (Have 'serena') { Say "  serena present ($(serena --version 2>$null))" }
  else {
    Say "  installing serena (uv tool; PyPI/dist name is serena-agent, command is serena)"
    uv tool install --from git+https://github.com/oraios/serena serena-agent
  }
  # Migrate an earlier uvx-based registration - a bare "already registered"
  # check would leave the slow, timeout-prone form in place forever.
  $serenaLine = (($mcpList -split "`r?`n") | Where-Object { $_ -match '^serena[: ]' }) -join ''
  if ($serenaLine -match 'uvx') {
    claude mcp remove --scope user serena 2>$null | Out-Null
    Say "  removed uvx-based serena registration (rebuilt from git on every launch)"
    $serenaLine = ''
  }
  if ($serenaLine) { Say "  serena already registered - skipped" }
  else {
    # --context claude-code is the current name of the old 'ide-assistant'
    # context (Serena logs a deprecation warning for the latter); same
    # toolset, shell/read/file-search tools excluded so it can't shadow
    # Bash+RTK or the built-in file tools.
    claude mcp add --scope user serena -- serena start-mcp-server --context claude-code
    Say "  serena registered at user scope (claude-code context: no shell/read tools)"
  }
  # Safety net for a genuinely cold first launch (uv tool run, LSP download):
  # Claude Code's default MCP startup timeout is 30s, which is not much.
  Set-GlobalEnvVar 'MCP_TIMEOUT' '120000'
  Set-SerenaDashboardConfig

  Say "serena autoinit - per-checkout project, automated (SessionStart hook)"
  Install-SerenaAutoInit

  Say "graphify - codebase knowledge graph"
  if (-not (Have 'graphify')) {
    Say "  installing graphify (PyPI package: graphifyy, double-y)"
    if (Have 'uv') { uv tool install 'graphifyy[all]' } else { pip install 'graphifyy[all]' }
  }
  graphify install 2>$null | Out-Null; Say "  /graphify skill installed (global)"
  # Deliberately NOT running `graphify claude install` here: it targets the
  # CLAUDE.md / .claude/settings.json in the CURRENT DIRECTORY, not this
  # script's global $ClaudeMd - wrong layer for a global install step. Its
  # PreToolUse Bash/Read/Glob hook also fires unconditionally on every
  # matching call (confirmed active, not a no-op) - noisier than contract
  # rule 1 below, which scopes graphify to architecture questions only. Wire
  # this into Init-Project instead if per-repo defense-in-depth is wanted.

  Say "graph autobuild - per-repo init, automated (SessionStart hook)"
  Install-GraphAutobuild

  Say "Headroom - proxy-layer compression (final pass before the API)"
  if (Have 'headroom') { Say "  headroom present ($(headroom --version 2>$null))" }
  else {
    Say "  installing headroom (PyPI package: headroom-ai)"
    if (Have 'uv') { uv tool install 'headroom-ai[all]' } else { pip install 'headroom-ai[all]' }
  }
  # Headroom integrates at the WIRE (the shim below), never as an MCP server.
  # A `headroom mcp serve` registration is not part of this stack and current
  # headroom-ai builds crash on its startup (AttributeError: 'Server' object
  # has no attribute 'list_tools'), so each session pays ~3s for a connection
  # that always fails, in every workspace. Drop a stray one.
  if ($mcpList -match '(?m)^headroom[: ]') {
    claude mcp remove --scope user headroom 2>$null | Out-Null
    Say "  removed stray headroom MCP registration (wire proxy is the integration, not MCP)"
  }
  # Newer headroom builds its own "tokensave" code graph by default - the
  # renamed, default-on incarnation of --code-graph, which the decisions log
  # forbids as a duplicate of graphify. Disable it when the flag exists;
  # probing keeps older headroom versions (no such flag) launching cleanly.
  $HeadroomFlags = ''
  if ((headroom wrap claude --help 2>$null | Out-String) -match '--no-tokensave') { $HeadroomFlags = ' --no-tokensave' }
  $global:LASTEXITCODE = 0
  Say "  shadowing bare 'claude' with a recursion-safe shim (see Install-ClaudeShim"
  Say "  for how the old self-recursion hazard is closed)"
  Install-ClaudeShim -HeadroomFlags $HeadroomFlags
  # The shim supersedes the 2.2 clw/hclaude/claudew wrapper - remove any of
  # ours a previous version wrote. Manual fallback is `headroom wrap claude`.
  $wrapBinDir = Join-Path $env:USERPROFILE '.local\bin'
  foreach ($old in @('clw', 'hclaude', 'claudew')) {
    $op = Join-Path $wrapBinDir "$old.ps1"
    if ((Test-Path $op) -and ((Get-Content -Raw $op) -match 'headroom wrap claude')) {
      Remove-Item -Force $op, (Join-Path $wrapBinDir "$old.cmd") -ErrorAction SilentlyContinue
      Say "  removed obsolete wrapper: $old (the shim replaces it)"
    }
  }
  Install-HeadroomCheck
  # Deliberately not passing --code-graph (would build a second structure graph,
  # duplicating graphify - rule 1 below already owns that question) or --memory
  # (this stack manages no intent/memory layer by design, see decisions log).

  Say "opensrc - dependency source fetcher (context tool, OUTSIDE the routing contract)"
  # Also not a routing layer: it answers one question the four tools can't -
  # "what does this dependency actually do" - by fetching the exact installed
  # version's source into a global cache (~/.opensrc, shared by all checkouts
  # and worktrees; zero per-repo state). Usage guidance lives in the opensrc
  # skill, not the contract. Non-fatal like every extra below.
  # Native exes don't throw on non-zero exit, so try/catch is useless here -
  # test $LASTEXITCODE explicitly, then reset it so it can't leak as our own.
  if (Have 'opensrc') { Say "  opensrc present" }
  elseif (Have 'npm') {
    npm install -g opensrc
    if ($LASTEXITCODE -eq 0) { Say "  opensrc installed (npm -g)" }
    else { Warn "npm install -g opensrc failed (exit $LASTEXITCODE) - install later, stack unaffected" }
    $global:LASTEXITCODE = 0
  } else { Warn "npm not found - skipping opensrc (npm install -g opensrc later)" }

  Say "worktrunk - parallel worktrees (workflow tool, OUTSIDE the routing contract)"
  # Not a token layer and deliberately absent from the contract below - it routes
  # nothing. It manages worktree lifecycle so parallel agents/tasks each get their
  # own checkout. One rule makes worktrees indistinguishable from any checkout:
  # the global post-start hook below re-runs the stack's per-checkout init
  # (graphify graph + rebuild hook) in every new worktree, but only for repos
  # whose primary checkout opted in (graphify-out/ exists). Every step here is
  # non-fatal: a worktrunk failure must never block the token stack.
  # Winget installs the binary as git-wt (avoids the Windows Terminal wt.exe
  # collision). NEVER detect via bare 'wt' here - that matches Windows Terminal's
  # launcher on stock Win11. Accept only git-wt or cargo's own wt.exe by path.
  # Winget puts portable exes in a package dir it adds to the USER PATH in the
  # registry - a shell started before that install (including the one running
  # this script right after installing) never sees it, so probe the package dir
  # directly instead of trusting Get-Command alone.
  function Find-WtBin {
    if (Have 'git-wt') { return 'git-wt' }
    $cargoWt = Join-Path $env:USERPROFILE '.cargo\bin\wt.exe'
    if (Test-Path $cargoWt) { return $cargoWt }
    $pkg = Get-ChildItem (Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages') `
      -Directory -Filter 'max-sixty.worktrunk_*' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($pkg) {
      $exe = Join-Path $pkg.FullName 'git-wt.exe'
      if (Test-Path $exe) { return $exe }
    }
    return $null
  }
  $WtBin = Find-WtBin
  if ($WtBin) { Say "  worktrunk present ($WtBin)" }
  else {
    Say "  installing worktrunk (winget: max-sixty.worktrunk, binary: git-wt)"
    if (Have 'winget') { winget install --id max-sixty.worktrunk --accept-source-agreements --accept-package-agreements }
    else { cargo install worktrunk }
    if ($LASTEXITCODE -ne 0) { Warn "worktrunk install failed (exit $LASTEXITCODE)" }
    $global:LASTEXITCODE = 0   # winget exit codes (e.g. 'no upgrade') must not leak as ours
    $WtBin = Find-WtBin
  }
  if ($WtBin) {
    & $WtBin config shell install
    if ($LASTEXITCODE -ne 0) { Warn "shell integration failed - run '$WtBin config shell install' manually" }
    $global:LASTEXITCODE = 0
    $WtCfgDir = Join-Path $env:APPDATA 'worktrunk'
    $WtCfg    = Join-Path $WtCfgDir 'config.toml'
    New-Item -ItemType Directory -Force -Path $WtCfgDir | Out-Null
    $wtExisting = if (Test-Path $WtCfg) { Get-Content -Raw $WtCfg } else { '' }
    if ($wtExisting -match 'claude-context-stack') {
      Say "  post-start hook already present - skipped"
    } elseif ($wtExisting -match '(?m)^\s*(\[\[?post-start|post-start\s*=)') {
      # Appending a second [post-start] table would make the whole TOML invalid
      # and break worktrunk entirely - never do it. Ask for a manual merge.
      Warn "config.toml already defines post-start - add this line to it manually:"
      Warn 'claude-context-stack = "[ -d ''{{ primary_worktree_path }}/graphify-out'' ] && graphify . && graphify hook install || true"'
    } else {
      # Hook body is POSIX sh: worktrunk runs hooks via Git for Windows' bash.
      $wtHook = @'

# claude-context-stack: replicate the stack's per-checkout state (graphify graph
# + post-commit rebuild hook) into every new worktree, only where the primary
# checkout was stack-inited. Delete this block to opt out.
[post-start]
claude-context-stack = "[ -d '{{ primary_worktree_path }}/graphify-out' ] && graphify . && graphify hook install || true"
'@
      # IO.File writes BOM-less UTF-8 on both PS 5.1 and 7; Add-Content -Encoding
      # utf8 on 5.1 stamps a BOM when creating the file, which TOML parsers reject.
      [IO.File]::AppendAllText($WtCfg, ($wtHook -replace "`r`n", "`n") + "`n")
      Say "  global post-start hook written -> $WtCfg"
    }
  } else {
    Warn "worktrunk unavailable - parallel-worktree support skipped (stack unaffected)"
  }

  Say "Extras' skills -> $ClaudeDir\skills (opensrc, worktrunk)"
  # Deployed unconditionally (even if a binary install above failed - both are
  # global tools the user may add later, and the worktrunk skill itself covers
  # offering the install) and idempotently: overwritten every run, like the
  # contract. See Install-ExtraSkill for source resolution.
  Install-ExtraSkill 'opensrc'
  Install-ExtraSkill 'worktrunk'

  Say "Routing contract -> $ClaudeMd"
  New-Item -ItemType Directory -Force -Path $ClaudeDir | Out-Null
  $existing = if (Test-Path $ClaudeMd) { Get-Content -Raw $ClaudeMd } else { '' }
  $stripped = [regex]::Replace($existing,
    '(?s)# >>> claude-context-stack >>>.*?# <<< claude-context-stack <<<\r?\n?', '')
  $out = ($stripped.TrimEnd() + "`r`n`r`n" + $Contract).TrimStart()
  Set-Content -Path $ClaudeMd -Value $out -Encoding utf8
  Say "  contract written (idempotent - re-running replaces the managed block)"

  Say "Condensed contract -> subagent files ($env:USERPROFILE\.claude\agents\)"
  Invoke-InjectCondensedContract (Join-Path $ClaudeDir 'agents')

  if (-not (Have 'rust-analyzer')) { Warn "rust-analyzer not on PATH - Serena needs it for Rust (rustup component add rust-analyzer)" }
  Write-Host ""; Say "Global install done. Open a NEW terminal so the claude shim takes effect."
  Say "No per-repo step needed - the first session in any git repo autobuilds its"
  Say "graph ('.\stack-init.ps1 init' still works for an eager build)."
}

function Init-Project {
  if (-not (Test-Path .git -PathType Container)) { Err "run from a git repo root (no .git here)"; exit 1 }
  if (-not (Have 'graphify')) { Err "graphify not installed - run '.\stack-init.ps1 global' first"; exit 1 }
  Say "building knowledge graph (graphify .)"; graphify .
  Say "installing local post-commit hook (incremental rebuild)"; graphify hook install
  Say "installing post-checkout/post-merge/post-rewrite refresh hooks"; Install-RefreshHooks
  if (-not ((Test-Path .gitignore) -and (Select-String -Path .gitignore -Pattern '^graphify-out/' -Quiet))) {
    Add-Content -Path .gitignore -Value "`r`n# Claude context-stack knowledge graph`r`ngraphify-out/" -Encoding utf8
    Say "gitignored graphify-out/"
  }
  Say "Condensed contract -> subagent files (.claude\agents\)"
  Invoke-InjectCondensedContract '.claude\agents'
  Write-Host ""; Say "Repo ready. First Claude session: let Serena onboard, then ask one"
  Say "architecture question and confirm it reads the graph instead of grepping."
}

function Get-Stats {
  $dir = Join-Path $ClaudeDir 'stack-stats'
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  $ts = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
  $snapPath = Join-Path $dir "$ts.json"
  if (Have 'rtk') { $rtkOut = (rtk gain 2>&1 | Out-String); $global:LASTEXITCODE = 0 } else { $rtkOut = 'rtk not on PATH' }
  if (Have 'headroom') { $headroomOut = (headroom stats 2>&1 | Out-String); $global:LASTEXITCODE = 0 } else { $headroomOut = 'headroom not installed' }
  @{ date = $ts; rtk_gain = $rtkOut; headroom_stats = $headroomOut } | ConvertTo-Json | Set-Content -Path $snapPath -Encoding utf8
  Say "  snapshot written -> $snapPath"
  $snaps = Get-ChildItem -Path $dir -Filter '*.json' | Sort-Object Name | Select-Object -Last 2
  if ($snaps) {
    Say "  last two snapshots:"
    foreach ($f in $snaps) {
      Write-Host "--- $($f.FullName) ---"
      Write-Host (Get-Content -Raw $f.FullName)
    }
  }
}

function Invoke-Verify {
  Say "verifying"
  $rtkHookActive = $false
  if (Have 'rtk') {
    Write-Host "  rtk:            OK ($(rtk --version 2>$null))"
    rtk gain *> $null
    $rtkHookActive = ($LASTEXITCODE -eq 0)
    $global:LASTEXITCODE = 0
  } else { Write-Host "  rtk:            NOT ON PATH" }
  if ($rtkHookActive) { Write-Host "  rtk hook:       active" } else { Write-Host "  rtk hook:       no stats yet (run a few Bash cmds)" }
  if ((claude mcp list 2>$null | Select-String -Quiet 'serena')) { Write-Host "  serena (mcp):   OK (user scope)" } else { Write-Host "  serena (mcp):   NOT registered" }
  if (Have 'graphify') { Write-Host "  graphify:       OK" } else { Write-Host "  graphify:       NOT installed" }
  if (Have 'headroom') { Write-Host "  headroom:       OK" } else { Write-Host "  headroom:       NOT installed" }
  $shimDir = Join-Path $ClaudeDir 'stack-bin'
  if (Test-Path (Join-Path $shimDir 'claude.ps1')) {
    $first = Get-Command claude -All -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($first -and $first.Source -like "$shimDir*") { Write-Host "  claude shim:    OK (bare 'claude' auto-wraps through headroom)" }
    else { Write-Host "  claude shim:    installed but NOT first on PATH (open a new terminal?)" }
  } else { Write-Host "  claude shim:    NOT installed" }
  $settingsPath = Join-Path $ClaudeDir 'settings.json'
  if ((Test-Path (Join-Path $ClaudeDir 'hooks\graph-autobuild.ps1')) -and (Test-Path $settingsPath) -and
      (Select-String -Path $settingsPath -Pattern 'graph-autobuild' -Quiet)) { Write-Host "  graph autobuild: OK (SessionStart)" }
  if ((Test-Path (Join-Path $ClaudeDir 'hooks\serena-autoinit.ps1')) -and (Test-Path $settingsPath) -and
      (Select-String -Path $settingsPath -Pattern 'serena-autoinit' -Quiet)) { Write-Host "  serena autoinit: OK (SessionStart)" }
  else { Write-Host "  serena autoinit: NOT registered" }
  else { Write-Host "  graph autobuild: NOT registered" }
  $wtFound = (Have 'git-wt') -or (Test-Path (Join-Path $env:USERPROFILE '.cargo\bin\wt.exe')) -or
    [bool](Get-ChildItem (Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages') -Directory -Filter 'max-sixty.worktrunk_*' -ErrorAction SilentlyContinue)
  if ($wtFound) { Write-Host "  worktrunk:      OK (workflow tool - outside the contract)" } else { Write-Host "  worktrunk:      NOT installed (optional)" }
  if (Have 'opensrc') { Write-Host "  opensrc:        OK (context tool - outside the contract)" } else { Write-Host "  opensrc:        NOT installed (optional)" }
  if (Test-Path (Join-Path $ClaudeDir 'skills\opensrc\SKILL.md'))   { Write-Host "  opensrc skill:    OK (global)" }   else { Write-Host "  opensrc skill:    NOT deployed - rerun global" }
  if (Test-Path (Join-Path $ClaudeDir 'skills\worktrunk\SKILL.md')) { Write-Host "  worktrunk skill:  OK (global)" } else { Write-Host "  worktrunk skill:  NOT deployed - rerun global" }
  if ((Test-Path $ClaudeMd) -and (Select-String -Path $ClaudeMd -Pattern 'claude-context-stack' -Quiet)) { Write-Host "  contract:       OK ($ClaudeMd)" } else { Write-Host "  contract:       MISSING" }
  if (Test-Path .git -PathType Container) {
    if (Test-Path graphify-out\graph.json) { $kb = "{0:N0} KB" -f ((Get-Item graphify-out\graph.json).Length/1KB); Write-Host "  graph (here):   OK ($kb)" } else { Write-Host "  graph (here):   not built - autobuilds next session (or run: .\stack-init.ps1 init)" }
    if (Test-Path .git\hooks\post-commit) { Write-Host "  post-commit:    OK" } else { Write-Host "  post-commit:    none" }
    $refreshHooksActive = $true
    foreach ($hook in 'post-checkout', 'post-merge', 'post-rewrite') {
      $hookPath = Join-Path (Join-Path $PWD.Path '.git\hooks') $hook
      if (-not ((Test-Path $hookPath) -and (Select-String -Path $hookPath -Pattern 'claude-context-stack:' -Quiet))) {
        $refreshHooksActive = $false
        break
      }
    }
    if ($refreshHooksActive) { Write-Host "  graph refresh:  OK (checkout/merge/rewrite)" } else { Write-Host "  graph refresh:  MISSING (checkout/merge/rewrite)" }
  }
}

switch ($Command.ToLower()) {
  'global'   { Install-Global }
  ''         { Install-Global }
  'init'     { Init-Project }
  'verify'   { Invoke-Verify }
  'contract' { if ($SubOption -eq '--condensed') { Write-Output $ContractCondensed } else { Write-Output $Contract } }
  'stats'    { Get-Stats }
  default    { Err "unknown command: $Command"; Write-Host "usage: .\stack-init.ps1 [global|init|verify|contract [--condensed]|stats]"; exit 1 }
}
# A stray $LASTEXITCODE from any native command above (pip/npm/winget/claude)
# must not become this script's exit code - completing the switch means success.
exit 0

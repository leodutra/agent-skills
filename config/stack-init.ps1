#Requires -Version 5.1
<#
=============================================================================
  Claude Code Context Stack  -  global installer  (Windows)
=============================================================================

  WHAT THIS IS
  A routing contract plus two components, built on one rule learned the hard
  way: eliminate waste at its source, never compress downstream.

    Serena    symbols    LSP over MCP (rust-analyzer / tsserver / pyright).
                         Kills RETRIEVAL+EDIT cost - exact symbol defs, refs,
                         diagnostics and symbol-level edits instead of
                         whole-file dumps and grep walls.
                         OPT-IN: registered but DISABLED. Its tool manifest is
                         a fixed per-session tax and it loses on cheap lookups,
                         so you turn it on with /mcp for refactor, test-writing
                         and architecture work on bigger repos (D53).
    ponytail  discipline Claude Code plugin (skill + SessionStart hook) that
                         injects a minimal-code ruleset. Default-on. Kills code
                         that never needed writing. Intercepts nothing - its
                         whole mechanism is text reaching the model (D54).

  REMOVED IN 3.0: graphify, RTK and Headroom. Headroom went on measurement -
  only 25% of the tokens it reported saving ever reached the wire, and four
  prefix-cache busts cost more than everything it saved (D49, D50, D51). RTK
  went because its numbers were never checked and it was inert in practice
  (D51). graphify went with all per-repo state (D52). Orientation and
  tool-output noise are now explicitly UNOWNED - the honest state, not a gap.

  DESIGN PRINCIPLE: prefer instructing over intercepting. Every layer removed
  in 3.0 sat in a path (before the shell, before the API, on disk) and each
  broke in a way that was a property of being there.

  WHAT IS GLOBAL vs PER-REPO
    Global (run once): Serena at user scope (registered, disabled) +
      serena-autoinit SessionStart hook (Serena does NOT activate from cwd on
      its own - it needs a .serena\project.yml, which that hook writes per
      checkout), the ponytail plugin, and the routing contract in
      %USERPROFILE%\.claude\CLAUDE.md.
    Per-repo: nothing. 3.0 holds no per-repo state and installs no git hooks.

  USAGE
    .\stack-init.ps1            # or: .\stack-init.ps1 global -> global install
    .\stack-init.ps1 skills     # list this repo's deployable skills
    .\stack-init.ps1 skills <name>...  # junction domain skills into this repo's
                                # .claude\skills (--copy for a committable copy)
    .\stack-init.ps1 verify     # check everything is wired
    .\stack-init.ps1 contract   # print the routing contract it installs
    .\stack-init.ps1 contract --condensed  # short form injected into agents
    .\stack-init.ps1 help       # print this banner

  The contract text itself is NOT in this script: it lives in contract.md and
  contract-condensed.md next to it, which stack-init.sh reads too, so the two
  installers cannot drift on the one artifact they both write.

  NOTE: `verify --docs` is deliberately NOT mirrored here (D42) - it is a
  maintenance check for whoever edits the doc set, not something a user runs.

  PREREQS: git, claude (Claude Code CLI), python3, node (ponytail's hooks), uv
  (Serena), Git for Windows. A language server per language. First run may need
  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned (or -ExecutionPolicy Bypass).
=============================================================================
#>
# ValueFromRemainingArguments rather than a plain [string]$SubOption: when run
# via -File, PowerShell's binder treats ANY argument starting with '-' as a
# parameter NAME, so `stack-init.ps1 contract --condensed` bound nothing, left
# $SubOption empty, and silently printed the FULL contract instead of the short
# form documented above. Remaining-argument capture takes '--condensed' as data.
param([string]$Command = 'global', [Parameter(ValueFromRemainingArguments = $true)][string[]]$Rest = @())
$ErrorActionPreference = 'Stop'

$ClaudeDir = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE '.claude' }
$ClaudeMd  = Join-Path $ClaudeDir 'CLAUDE.md'
# The generated SessionStart hook is also the ONE implementation of "give this
# checkout its git hooks": `init` runs it with -Hooks rather than carrying a
# second copy of the same three hook bodies (which is what it used to do, minus
# the post-commit pin repair the copy never learned about).
$GraphAutobuildHook = Join-Path $ClaudeDir 'hooks\graph-autobuild.ps1'
function Say ($m){ Write-Host "==> "   -ForegroundColor Green  -NoNewline; Write-Host $m }
function Warn($m){ Write-Host "warn: " -ForegroundColor Yellow -NoNewline; Write-Host $m }
function Err ($m){ Write-Host "error: "-ForegroundColor Red    -NoNewline; Write-Host $m }
function Have($c){ [bool](Get-Command $c -ErrorAction SilentlyContinue) }

# Windows PowerShell 5.1's `Set-Content -Encoding utf8` stamps a UTF-8 BOM, and
# this script runs under 5.1 as often as under 7. In JSON a BOM is a spec
# violation: Python's json.load() rejects it, which is exactly how the POSIX
# installer's merge helper reads the SAME settings.json - so a file written here
# used to be unreadable there. Write BOM-less UTF-8 from one place instead; it
# matches both PowerShell 7 and stack-init.sh byte for byte.
$Utf8NoBom = New-Object System.Text.UTF8Encoding $false
function Write-Utf8 ($Path, $Text) {
  $dir = Split-Path $Path
  if ($dir) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  # Always end with exactly one newline. Here-strings and ConvertTo-Json both
  # end WITHOUT one, and WriteAllText adds nothing - a file with no final
  # newline is precisely what makes a later append glue onto its last line.
  [IO.File]::WriteAllText($Path, (($Text -replace '[\r\n]+$', '') + "`r`n"), $Utf8NoBom)
}

function Read-Text ($Path) {
  # `Get-Content -Raw` returns $null - not '' - for an EMPTY file, and every
  # caller here feeds the result to [regex]::Replace or .Contains, both of which
  # throw on null. Under $ErrorActionPreference='Stop' that aborted the whole
  # global install on something as ordinary as an empty ~/.claude/CLAUDE.md.
  # A leading BOM is stripped too, so callers matching '^...' see the real text.
  # Spelled [char]0xFEFF, never as a literal: this script has no BOM of its own,
  # and Windows PowerShell 5.1 decodes a BOM-less .ps1 as ANSI, which would turn
  # an embedded U+FEFF into three junk characters that match nothing.
  if (-not (Test-Path $Path)) { return '' }
  $t = Get-Content -Raw $Path -ErrorAction SilentlyContinue
  if ($null -eq $t) { return '' }
  return ($t -replace "^$([char]0xFEFF)", '')
}

function Write-ManagedBlock ($Path, $Block) {
  # Replace our delimited block, leaving everything else in the file alone.
  # TrimEnd/TrimStart normalise to exactly one blank line before the block no
  # matter how the host document was left, so re-running never drifts.
  $stripped = [regex]::Replace((Read-Text $Path),
    '(?s)# >>> claude-context-stack >>>.*?# <<< claude-context-stack <<<\r?\n?', '')
  Write-Utf8 $Path (($stripped.TrimEnd() + "`r`n`r`n" + $Block).TrimStart())
}

# The contract text is NOT duplicated in this script. Both installers read the
# same two files next to them, so the Windows and POSIX variants cannot drift -
# they already had (hyphens here, em dashes there) while claiming to write the
# same managed block into the same ~\.claude\CLAUDE.md. Those files are
# ASCII-only on purpose: Read-Text goes through Get-Content, and Windows
# PowerShell 5.1 decodes a BOM-less file as ANSI, which would turn any non-ASCII
# byte into mojibake in the contract it writes.
function Get-Contract {
  param([string]$File)
  $p = Join-Path $PSScriptRoot $File
  if (-not (Test-Path $p)) {
    Err "contract source missing: $p"
    Err "run stack-init from the agent-skills repo checkout (config\ ships these)"
    exit 1
  }
  return (Read-Text $p).TrimEnd()
}

# Skills for the extras (gauntlet-loop, opensrc, worktrunk). These ship none of
# their own, and without a SKILL.md in
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
  # One guard, not two: Get-ChildItem on a missing directory returns nothing
  # under -ErrorAction SilentlyContinue, so the container test was redundant.
  $files = Get-ChildItem -Path $Dir -Filter '*.md' -File -ErrorAction SilentlyContinue
  if (-not $files) {
    Say "  no agent files at $Dir - skipping condensed contract injection"
    return
  }
  $block = Get-Contract 'contract-condensed.md'
  foreach ($f in $files) { Write-ManagedBlock $f.FullName $block }
  Say "  condensed contract injected into $Dir\*.md"
}

function Check-Deps {
  $miss = $false
  foreach ($d in 'git','claude') { if (-not (Have $d)) { Err "missing required: $d"; $miss = $true } }
  if (-not (Have 'cargo')) { Warn "cargo not found - needed to install RTK" }
  if ($miss) { Err "install the required tools above, then re-run"; exit 1 }
}

function Get-GitHooksDir {
  # Ask git for the hooks dir instead of assuming .git\hooks. In a LINKED
  # WORKTREE .git is a FILE, not a directory, so .git\hooks does not exist and
  # writing there either fails or drops hooks somewhere git never reads.
  # `rev-parse --git-path hooks` resolves core.hooksPath and worktrees alike,
  # and points every worktree at the COMMON hooks dir - which is what we want:
  # git supports one hooks dir per repo, and the bodies below are cwd-relative,
  # so they act on whichever worktree ran the command.
  # [IO.File] resolves relative paths against .NET's process-wide current
  # directory, which does NOT track PowerShell's Set-Location/Push-Location -
  # always resolve to an absolute path via $PWD first, or this can write into
  # whatever directory the process originally launched from instead of cwd.
  $p = git rev-parse --git-path hooks 2>$null
  if (-not $p) { return $null }
  if (-not [IO.Path]::IsPathRooted($p)) { $p = Join-Path $PWD.Path $p }
  return [IO.Path]::GetFullPath($p)
}

function Test-InGitRepo {
  # `.git` is a DIRECTORY only in the primary checkout - in a linked worktree it
  # is a FILE pointing at the common dir, so `Test-Path .git -PathType Container`
  # is false and every worktree gets locked out of `init` and of verify's
  # repo-local checks. Ask git instead, which answers the same in both.
  $null = git rev-parse --git-dir 2>$null
  $ok = ($LASTEXITCODE -eq 0)
  $global:LASTEXITCODE = 0
  return $ok
}

function Find-WtBin {
  # Winget installs the binary as git-wt (avoids the Windows Terminal wt.exe
  # collision). NEVER detect via bare 'wt' here - that matches Windows Terminal's
  # launcher on stock Win11. Accept only git-wt or cargo's own wt.exe by path.
  # Winget puts portable exes in a package dir it adds to the USER PATH in the
  # registry - a shell started before that install (including the one running
  # this script right after installing) never sees it, so probe the package dir
  # directly instead of trusting Get-Command alone.
  # Shared with Invoke-Verify, which used to inline a LOOSER copy of this: it
  # accepted the winget package DIRECTORY without checking git-wt.exe inside it,
  # so a leftover dir from an uninstall reported worktrunk as present.
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

function Install-Uv {
  if (Have 'uv') { return }
  Say "  installing uv (needed to run Serena)"
  if (Have 'winget') { winget install --id astral-sh.uv -e --silent }
  else { powershell -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex" }
  if (-not (Have 'uv')) { Warn "uv install failed - Serena will not be able to launch" }
}

$SettingsPath = Join-Path $ClaudeDir 'settings.json'

function Read-Settings {
  # A settings.json that exists but does not parse is a HARD STOP, never an
  # empty object. The old `catch { $data = @{} }` meant one malformed byte -
  # a stray comma, a half-finished hand edit - silently discarded the user's
  # ENTIRE config on the next write: RTK's PreToolUse hook, every permission,
  # every env var. Failing to install a hook is recoverable; that is not.
  $raw = Read-Text $SettingsPath
  if (-not $raw.Trim()) { return [PSCustomObject]@{} }
  try { return ($raw | ConvertFrom-Json) }
  catch {
    Err "$SettingsPath is not valid JSON - fix or move it, then re-run"
    Err "(refusing to overwrite it: that would drop RTK's hook and your permissions)"
    exit 1
  }
}

function Save-Settings {
  param($Data)
  Write-Utf8 $SettingsPath ($Data | ConvertTo-Json -Depth 20)
}

function Register-SessionStartHook {
  # Adds a SessionStart command hook to global settings.json (idempotent) and
  # returns the parsed settings object so callers can inspect other hooks.
  param([string]$Cmd)
  $data = Read-Settings
  if (-not $data.PSObject.Properties['hooks']) { $data | Add-Member -NotePropertyName hooks -NotePropertyValue ([PSCustomObject]@{}) }
  if (-not $data.hooks.PSObject.Properties['SessionStart']) { $data.hooks | Add-Member -NotePropertyName SessionStart -NotePropertyValue @() }
  $starts = @($data.hooks.SessionStart)
  $already = $starts | Where-Object { $_.hooks | Where-Object { $_.command -eq $Cmd } }
  if (-not $already) {
    $starts += [PSCustomObject]@{ hooks = @([PSCustomObject]@{ type = 'command'; command = $Cmd }) }
    $data.hooks.SessionStart = $starts
  }
  Save-Settings $data
  return $data
}

function Set-GlobalEnvVar {
  # Writes settings.json env.<Name> unless the user already set it (their value
  # wins - this is a floor, not a policy).
  param([string]$Name, [string]$Value)
  $data = Read-Settings
  if (-not $data.PSObject.Properties['env']) { $data | Add-Member -NotePropertyName env -NotePropertyValue ([PSCustomObject]@{}) }
  if ($data.env.PSObject.Properties[$Name]) {
    Say "  settings.json env.$Name already set ($($data.env.$Name)) - left alone"
    return
  }
  $data.env | Add-Member -NotePropertyName $Name -NotePropertyValue $Value
  Save-Settings $data
  Say "  settings.json env.$Name = $Value"
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
  Write-Utf8 $serenaPath @'
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

$gd = git rev-parse --git-dir 2>$null
if (-not $gd) { exit 0 }
if (-not [IO.Path]::IsPathRooted($gd)) { $gd = Join-Path $top $gd }
$cgd = git rev-parse --git-common-dir 2>$null
if (-not $cgd) { $cgd = $gd }
elseif (-not [IO.Path]::IsPathRooted($cgd)) { $cgd = Join-Path $top $cgd }
# GetFullPath, not Resolve-Path: normalises without touching the filesystem, so
# a worktree whose git dir has been pruned still compares cleanly.
$isMain = ([IO.Path]::GetFullPath($gd) -eq [IO.Path]::GetFullPath($cgd))

$proj   = Join-Path $top '.serena/project.yml'
$marker = 'Generated by claude-context-stack (serena-autoinit)'

# Keep the generated folder out of git without touching a tracked .gitignore -
# same rule the graph autobuild hook follows. Written to the COMMON git dir so
# one entry covers the main checkout and every worktree hanging off it.
function Set-SerenaExcluded {
  $infoDir = Join-Path $cgd 'info'
  New-Item -ItemType Directory -Force -Path $infoDir | Out-Null
  $excl = Join-Path $infoDir 'exclude'
  if (-not ((Test-Path $excl) -and (Select-String -Path $excl -Pattern '^\.serena/$' -Quiet))) {
    Add-Content -Path $excl -Value "`n.serena/"
  }
}

# Writing project.yml does NOT make Serena use it: the MCP server starts with NO
# active project, and every symbol tool then fails with "No active project" until
# something calls activate_project. That failure is silent - the model just falls
# back to grep, breaking contract rule 2 with nothing in the UI to say so. So the
# hook ALWAYS ends by naming the project to activate, whether it wrote one,
# repaired one, or found a good one already there.
function Send-Activation ($projPath, $projName, $extra) {
  Set-SerenaExcluded
  $msg = "Serena project for this checkout: '$projName' at $projPath. Serena starts " +
         "with NO active project - call activate_project with that path before the " +
         "first symbol query, and whenever a tool answers 'No active project'."
  if ($extra) { $msg = "$msg $extra" }
  @{ hookSpecificOutput = @{ hookEventName = 'SessionStart'; additionalContext = $msg } } |
    ConvertTo-Json -Compress
  exit 0
}

# Falls back to $name (derived below), so a config with no project_name key
# still yields the branch-suffixed name a linked worktree needs.
function Get-ProjectName ($path) {
  foreach ($line in (Get-Content $path)) {
    if ($line -match '^\s*project_name\s*:\s*"?([^"\r\n]+?)"?\s*$') { return $matches[1] }
  }
  return $name
}

# Entries of the YAML `language_servers:` block. Only `- name` lines are
# collected, so scanning past blank/comment lines to the next real key cannot
# invent entries; the first non-list, non-blank, non-comment line ends the block.
function Get-ConfiguredServers ($path) {
  $found = [System.Collections.Generic.List[string]]::new()
  $inList = $false
  foreach ($line in (Get-Content $path)) {
    if ($line -match '^\s*language_servers\s*:') { $inList = $true; continue }
    if (-not $inList) { continue }
    if ($line -match '^\s*-\s*"?([A-Za-z0-9_]+)"?\s*$') { $found.Add($matches[1].ToLower()) }
    elseif ($line -match '^\s*(#.*)?$') { continue }
    else { break }
  }
  return $found
}

function Write-ProjectYml ($path, $projName, $srv, $mainCheckout) {
  $lines = [System.Collections.Generic.List[string]]::new()
  $lines.Add('# Generated by claude-context-stack (serena-autoinit). Safe to edit or')
  $lines.Add('# delete: while this header is present the file is left alone. A config')
  $lines.Add('# WITHOUT this header came from Serena auto-detection and is repaired')
  $lines.Add('# (original kept as project.yml.bak-*) when its language_servers list')
  $lines.Add('# misses a language present in this checkout. Machine-local overrides')
  $lines.Add('# belong in project.local.yml, which Serena ignores by default.')
  $lines.Add('project_name: "' + $projName + '"')
  $lines.Add('language_servers:')
  foreach ($s in $srv) { $lines.Add("- $s") }
  $lines.Add('ignore_all_files_in_gitignore: true')
  if ($mainCheckout) {
    # Worktrunk nests linked worktrees at .claude\worktrees\ INSIDE the main
    # checkout, so without this the main project indexes every worktree as well
    # and one symbol lookup returns a near-duplicate hit per branch. Emitted
    # unconditionally: worktrees usually appear after this file is generated,
    # and it is inert when the directory does not exist.
    $lines.Add('ignored_paths:')
    $lines.Add('- ".claude/worktrees"')
  }
  New-Item -ItemType Directory -Force -Path (Split-Path $path) | Out-Null
  # WriteAllText with an explicit no-BOM encoder rather than Set-Content: this
  # hook is registered as `powershell -NoProfile ...`, i.e. Windows PowerShell
  # 5.1, whose `-Encoding utf8` prepends a BOM. PyYAML and ruamel both strip a
  # leading BOM, so it parses either way - but this keeps the file byte-identical
  # to the POSIX variant's output instead of depending on that tolerance.
  [IO.File]::WriteAllText($path, (($lines -join "`n") + "`n"),
    (New-Object System.Text.UTF8Encoding $false))
}

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
if (-not $exts) {
  if (Test-Path $proj) { Send-Activation $top (Get-ProjectName $proj) }
  exit 0
}

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
if ($servers.Count -eq 0) {
  if (Test-Path $proj) { Send-Activation $top (Get-ProjectName $proj) }
  exit 0
}

if (Test-Path $proj) {
  $existingText = Get-Content -Raw $proj
  $existingName = Get-ProjectName $proj
  # Ours already: left alone for good, so hand edits to it survive every session.
  if ($existingText -and $existingText.Contains($marker)) { Send-Activation $top $existingName }
  # Not ours, so Serena's own auto-detection wrote it - and that detection is too
  # weak to leave in place: on this very repo (mostly markdown, one .sh, one .ps1)
  # it selected `powershell` ALONE, so get_symbols_overview on any .md or .sh
  # answered "Cannot extract symbols ... Active language servers: ['powershell']"
  # and the model silently fell back to grep. Repair only when the file actually
  # misses a language present here, and never destroy the original.
  $configured = Get-ConfiguredServers $proj
  $missing = @($servers | Where-Object { $configured -notcontains $_ })
  if ($missing.Count -eq 0) { Send-Activation $top $existingName }
  $bak = "$proj.bak-" + (Get-Date -Format 'yyyyMMddHHmmss')
  Copy-Item -Force $proj $bak
  # Repair fixes only what was broken: the name it was registered under is kept,
  # so an intentionally renamed project does not silently change identity.
  Write-ProjectYml $proj $existingName $servers $isMain
  Send-Activation $top $existingName ("Its language_servers were repaired (had: " +
    (($configured -join ', ')) + "; missing: " + (($missing -join ', ')) +
    "); the previous file is kept at $bak.")
}

Write-ProjectYml $proj $name $servers $isMain
Send-Activation $top $name
'@

  Register-SessionStartHook "powershell -NoProfile -ExecutionPolicy Bypass -File `"$serenaPath`"" | Out-Null
  Say "  SessionStart serena-autoinit hook installed (opt out: CLAUDE_STACK_NO_SERENA_INIT=1 or .serena-skip)"
}

function Install-Ponytail {
  # ponytail ships as a Claude Code plugin from a GitHub-backed marketplace.
  # `claude plugin` drives both steps non-interactively, which is the only reason
  # an installer can do this at all - the /plugin slash commands cannot be
  # scripted, and interactively they must be sent as two SEPARATE prompts.
  # Non-fatal throughout (D32): a session without the ruleset is worse, not broken.
  if (-not (Have 'node')) {
    Warn "node not on PATH - ponytail's lifecycle hooks need it. Its skills still"
    Warn "  work; the always-on activation just stays quiet instead of erroring."
  }
  if ((claude plugin list 2>$null | Out-String) -match '(?i)ponytail') {
    Say "  ponytail already installed - skipped"
    $global:LASTEXITCODE = 0
    return
  }
  claude plugin marketplace add DietrichGebert/ponytail 2>$null | Out-Null
  if ($LASTEXITCODE -ne 0) { Warn "could not add the ponytail marketplace - skipping plugin install" }
  claude plugin install ponytail@ponytail 2>$null | Out-Null
  if ($LASTEXITCODE -eq 0) { Say "  ponytail installed (minimal-code ruleset injected at session start)" }
  else {
    Warn "claude plugin install ponytail@ponytail failed - install it by hand:"
    Warn "  /plugin marketplace add DietrichGebert/ponytail"
    Warn "  /plugin install ponytail@ponytail      (two SEPARATE prompts)"
  }
  $global:LASTEXITCODE = 0
}

function Install-ContractRefresh {
  # The condensed contract was written into agent files ONLY at install time, so
  # editing contract-condensed.md left every deployed copy stale until somebody
  # re-ran the installer - the same drift removed from the contract text itself
  # one level up, reintroduced one level down. Every comparable per-repo concern
  # had already become a self-healing SessionStart hook (the graph, then Serena);
  # this was the one that had not.
  #
  # Scope is ~\.claude\agents\ ONLY, deliberately. .claude\agents\ is TRACKED,
  # and a background job must never mutate files the user would have to commit
  # (the rule the graph autobuild follows by writing solely under .git\). The
  # per-repo copies stay with `init`, where a human asked for them.
  #
  # The hook reads contract-condensed.md live, through an absolute path resolved
  # now - baking the TEXT in would recreate exactly the staleness this fixes.
  $src = Join-Path $PSScriptRoot 'contract-condensed.md'
  $agents = Join-Path $ClaudeDir 'agents'
  $hookPath = Join-Path $ClaudeDir 'hooks\contract-refresh.ps1'
  $tpl = @'
# claude-context-stack: refresh the condensed routing contract in user-global
# agent files at session start. Opt out: CLAUDE_STACK_NO_CONTRACT_REFRESH=1.
# Uninstall: remove the SessionStart entry in settings.json.
if ($env:CLAUDE_STACK_NO_CONTRACT_REFRESH) { exit 0 }
$src = '__SRC__'
$dir = '__DIR__'
if (-not (Test-Path $src)) { exit 0 }
if (-not (Test-Path $dir)) { exit 0 }
$block = Get-Content -Raw $src -ErrorAction SilentlyContinue
if (-not $block) { exit 0 }
$block = ($block -replace "^$([char]0xFEFF)", '').TrimEnd()
$marker = '(?s)# >>> claude-context-stack >>>.*?# <<< claude-context-stack <<<'
# Silent by design - a session-start hook that cannot write a file the user did
# not ask about should not editorialise about it.
foreach ($f in (Get-ChildItem -Path $dir -Filter '*.md' -File -ErrorAction SilentlyContinue)) {
  $text = Get-Content -Raw $f.FullName -ErrorAction SilentlyContinue
  if ($null -eq $text) { continue }
  $text = $text -replace "^$([char]0xFEFF)", ''
  # Skip files already carrying the current text: the common case is no change
  # at all, and rewriting every agent file every session churns mtimes for
  # nothing.
  $cur = [regex]::Match($text, $marker)
  if ($cur.Success -and ($cur.Value.TrimEnd() -eq $block)) { continue }
  $stripped = [regex]::Replace($text, ($marker + '\r?\n?'), '')
  $new = ($stripped.TrimEnd() + "`r`n`r`n" + $block).TrimStart() + "`r`n"
  try {
    [IO.File]::WriteAllText($f.FullName, $new, (New-Object Text.UTF8Encoding $false))
  } catch { continue }
}
exit 0
'@
  $tpl = $tpl.Replace('__SRC__', $src.Replace("'", "''")).Replace('__DIR__', $agents.Replace("'", "''"))
  Write-Utf8 $hookPath $tpl
  Register-SessionStartHook "powershell -NoProfile -ExecutionPolicy Bypass -File `"$hookPath`"" | Out-Null
  Say "  SessionStart contract-refresh hook installed (~\.claude\agents only; opt out: CLAUDE_STACK_NO_CONTRACT_REFRESH=1)"
}

function Set-SerenaDashboardConfig {
  # Dashboards stay enabled (one per session, own port each) but no longer
  # auto-open a browser tab per Claude session; the global tray icon
  # (tray_manager) lists every running instance instead. Unconditional here
  # because Serena documents tray_manager as fully supported on Windows. The
  # sh installer reaches the same end state but has to EARN it: it probes the
  # session bus for a StatusNotifier host and asks pystray which backend it
  # bound, falling back to a pinned `browser` when either answer says no.
  $cfg = Join-Path $env:USERPROFILE '.serena\serena_config.yml'
  if (-not (Test-Path $cfg)) {
    Say "  serena_config.yml not found (Serena writes it on first launch) - rerun global later to apply dashboard settings"
    return
  }
  $text = Read-Text $cfg
  # [^\r\n]* instead of .*$ - in .NET regex `.` matches \r, so .*$ would eat
  # the CR of CRLF files and dirty the diff on every run. (Plain ASCII hyphen:
  # the file carries no BOM, so 5.1 decodes it as ANSI and any non-ASCII byte
  # here would come back as mojibake.)
  $new = $text -replace '(?m)^web_dashboard_open_on_launch:[^\r\n]*', 'web_dashboard_open_on_launch: false'
  $new = $new -replace '(?m)^web_dashboard_interface:[^\r\n]*', 'web_dashboard_interface: tray_manager'
  if ($new -ne $text) {
    Write-Utf8 $cfg $new
    Say "  serena dashboard: auto-open off; tray_manager icon lists all instances"
  } else {
    Say "  serena dashboard settings already applied"
  }
}

function Install-Global {
  Check-Deps
  # One health-check pass: `claude mcp list` spawns every registered server and
  # waits on it, so calling it twice doubles the slowest step in this function.
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
  elseif (Have 'uv') {
    Say "  installing serena (uv tool; PyPI/dist name is serena-agent, command is serena)"
    uv tool install --from git+https://github.com/oraios/serena serena-agent
  }
  else { Warn "uv missing - cannot install serena; symbol routing (contract rule 2) stays unavailable" }
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
    # toolset, shell/read/file-search tools excluded. The shell exclusion is a
    # PERMISSION boundary, not a compression one (D56): Claude Code gates Bash
    # per command and MCP tools per tool, so an approved execute_shell_command
    # would be one blanket grant over every command it ever runs.
    claude mcp add --scope user serena -- serena start-mcp-server --context claude-code
    Say "  serena registered at user scope (claude-code context: no shell/read tools)"
  }
  # Registered but NOT enabled (D53). Serena's tool manifest is a fixed
  # per-session tax whether or not a symbol tool is ever called, and it loses on
  # cheap lookups. Leaving it off makes enabling it a deliberate /mcp step.
  claude mcp disable serena 2>$null | Out-Null
  if ($LASTEXITCODE -eq 0) { Say "  serena DISABLED by default - enable per session with /mcp (D53)" }
  else { Warn "could not disable serena (older claude?) - it will load in every session" }
  $global:LASTEXITCODE = 0
  # Safety net for a genuinely cold first launch (uv tool run, LSP download):
  # Claude Code's default MCP startup timeout is 30s, which is not much.
  Set-GlobalEnvVar 'MCP_TIMEOUT' '120000'
  Set-SerenaDashboardConfig

  Say "serena autoinit - per-checkout project, automated (SessionStart hook)"
  Install-SerenaAutoInit

  Say "ponytail - minimal-code discipline (Claude Code plugin, default-on)"
  Install-Ponytail

  Say "opensrc - dependency source fetcher (context tool, OUTSIDE the routing contract)"
  # Also not a routing layer: it answers a question neither component covers -
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
  # own checkout. Every step here is non-fatal: a worktrunk failure must never
  # block the stack.
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
    # 3.0 writes NO post-start hook. It existed to replicate graphify's per-repo
    # graph and rebuild hook into each new worktree; graphify is gone (D52) and
    # the only per-checkout state left is .serena\project.yml, which
    # serena-autoinit already writes at every session start.
    $WtCfg = Join-Path (Join-Path $env:APPDATA 'worktrunk') 'config.toml'
    if ((Test-Path $WtCfg) -and ((Get-Content -Raw $WtCfg) -match 'claude-context-stack')) {
      $keep = @(); $skip = $false
      foreach ($ln in (Get-Content $WtCfg)) {
        if ($ln -match '^# claude-context-stack: replicate') { $skip = $true; continue }
        if ($skip -and $ln -match '^claude-context-stack = ') { $skip = $false; continue }
        if (-not $skip) { $keep += $ln }
      }
      [IO.File]::WriteAllText($WtCfg, (($keep -join "`n") + "`n"))
      Say "  removed obsolete graphify post-start hook from $WtCfg (D52)"
    }
  } else {
    Warn "worktrunk unavailable - parallel-worktree support skipped (stack unaffected)"
  }

  Say "Extras' skills -> $ClaudeDir\skills (gauntlet-loop, opensrc, worktrunk)"
  # Deployed unconditionally (even if a binary install above failed - both are
  # global tools the user may add later, and the worktrunk skill itself covers
  # offering the install) and idempotently: overwritten every run, like the
  # contract. See Install-ExtraSkill for source resolution.
  Install-ExtraSkill 'gauntlet-loop'
  Install-ExtraSkill 'opensrc'
  Install-ExtraSkill 'worktrunk'

  Say "Routing contract -> $ClaudeMd"
  Write-ManagedBlock $ClaudeMd (Get-Contract 'contract.md')
  Say "  contract written (idempotent - re-running replaces the managed block)"

  Say "Condensed contract -> subagent files ($env:USERPROFILE\.claude\agents\)"
  Invoke-InjectCondensedContract (Join-Path $ClaudeDir 'agents')
  # ...and keep them current between installs. Only the user-global copies:
  # .claude\agents\ is tracked, so it stays with `init` (see the function).
  Install-ContractRefresh

  if (-not (Have 'rust-analyzer')) { Warn "rust-analyzer not on PATH - Serena needs it for Rust (rustup component add rust-analyzer)" }
  Write-Host ""; Say "Global install done. Open a NEW terminal so the claude shim takes effect."
  Say "No per-repo step needed - the first session in any git repo autobuilds its"
  Say "graph ('.\stack-init.ps1 init' still works for an eager build)."
}

# Per-repo skill deployment (`skills`). The global install deploys exactly
# three skills (gauntlet-loop, opensrc, worktrunk) because they are
# project-agnostic; the repo's DOMAIN skills (architecture-blueprint,
# rust-bevy-architecture, rust-wgpu-functional, macro-analyst) stay out of
# $ClaudeDir\skills on purpose: every skill there pays its description into
# EVERY session's context, in every project, relevant or not. This deploys
# them into the CURRENT repo's .claude\skills instead, where only sessions in
# that repo pay for them.
#
# Junction by default (the Windows counterpart of stack-init.sh's symlink:
# needs no Developer Mode or elevation, unlike -ItemType SymbolicLink), copy
# on --copy. A junction stays current with this checkout automatically but
# targets an absolute path on THIS machine, so it goes into .git\info\exclude;
# --copy is committable/portable, refreshed only by re-running, and taken OUT
# of the exclude. Copies carry a marker file so a refresh only ever deletes a
# directory this command created - a user's own same-named skill is refused,
# never clobbered.
$SkillCopyMarker = '.claude-context-stack'

function Get-RepoSkillNames {
  Get-ChildItem -Path (Join-Path $PSScriptRoot '..\skills') -Directory -ErrorAction SilentlyContinue |
    Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } |
    ForEach-Object { $_.Name }
}

function Show-RepoSkills {
  $top = $null
  if (Test-InGitRepo) { $top = git rev-parse --show-toplevel 2>$null }
  Say ("deployable skills (canonical: " + (Join-Path $PSScriptRoot '..\skills') + ")")
  foreach ($name in Get-RepoSkillNames) {
    $state = @()
    if (Test-Path (Join-Path $ClaudeDir "skills\$name\SKILL.md")) { $state += 'global' }
    if ($top) {
      $dst = Join-Path $top ".claude\skills\$name"
      if (Test-Path $dst) {
        if ((Get-Item $dst -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { $state += 'linked here' }
        else { $state += 'copied here' }
      }
    }
    Write-Row $name $(if ($state.Count) { $state -join ', ' } else { 'not deployed' })
  }
  if (-not $top) { Say '  (not in a git repo - per-repo state not shown)' }
}

# Exact-line add/remove on the COMMON git dir's info\exclude, so one entry
# covers the main checkout and every linked worktree (same rule the hooks
# follow). Exact match on both sides: these must never eat a broader
# user-written pattern that merely contains the same text.
function Add-ExcludeLine {
  param([string]$Cgd, [string]$Line)
  $dir = Join-Path $Cgd 'info'
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  $f = Join-Path $dir 'exclude'
  $text = Read-Text $f
  if (($text -split "\r?\n") -notcontains $Line) {
    Write-Utf8 $f (($text.TrimEnd() + "`r`n" + $Line).TrimStart())
  }
}
function Remove-ExcludeLine {
  param([string]$Cgd, [string]$Line)
  $f = Join-Path $Cgd 'info\exclude'
  if (-not (Test-Path $f)) { return }
  $lines = (Read-Text $f) -split "\r?\n"
  if ($lines -notcontains $Line) { return }
  Write-Utf8 $f (($lines | Where-Object { $_ -ne $Line }) -join "`r`n")
}

function Deploy-RepoSkills {
  param([string[]]$SkillArgs = @())
  $copyMode = $false; $names = @()
  foreach ($a in $SkillArgs) {
    if ($a -in '--copy', '-copy') { $copyMode = $true }
    elseif ($a -like '-*') { Err "unknown flag: $a"; Write-Host 'usage: .\stack-init.ps1 skills [--copy] [<name>...]'; exit 1 }
    else { $names += $a }
  }
  if (-not $names.Count) { Show-RepoSkills; return }
  if (-not (Test-InGitRepo)) { Err "run from a git repo - skills deploy into the repo's .claude\skills"; exit 1 }
  $top = git rev-parse --show-toplevel 2>$null
  if (-not $top) { Err 'could not resolve the repo root'; exit 1 }
  $cgd = git rev-parse --git-common-dir 2>$null
  if (-not $cgd) { $cgd = git rev-parse --git-dir 2>$null }
  if (-not [IO.Path]::IsPathRooted($cgd)) { $cgd = Join-Path $top $cgd }
  New-Item -ItemType Directory -Force -Path (Join-Path $top '.claude\skills') | Out-Null
  $fail = $false
  foreach ($name in $names) {
    $src = Join-Path $PSScriptRoot "..\skills\$name"
    if (-not (Test-Path (Join-Path $src 'SKILL.md'))) {
      Err "no such skill: $name (available: $((Get-RepoSkillNames) -join ' '))"
      $fail = $true; continue
    }
    $src = (Resolve-Path $src).Path
    $dst = Join-Path $top ".claude\skills\$name"
    # No trailing slash: a slash-terminated gitignore pattern matches only real
    # directories, and a junction/symlink is not one to git - the slashed form
    # silently failed to exclude it. Forward slashes: gitignore syntax, not a
    # filesystem path.
    $line = "/.claude/skills/$name"
    $existing = if (Test-Path $dst) { Get-Item $dst -Force } else { $null }
    $isLink = $existing -and ($existing.Attributes -band [IO.FileAttributes]::ReparsePoint)
    $isOurCopy = $existing -and -not $isLink -and (Test-Path (Join-Path $dst $SkillCopyMarker))
    if ($existing -and -not $isLink -and -not $isOurCopy) {
      Warn "${name}: $dst exists and was not deployed by this command - remove it yourself first"
      $fail = $true; continue
    }
    # [IO.Directory]::Delete removes a junction WITHOUT following it into the
    # target; Remove-Item -Recurse on a reparse point has deleted target
    # contents on older PowerShell, so it is never used on one.
    if ($isLink) { [IO.Directory]::Delete($dst) }
    elseif ($isOurCopy) { Remove-Item -Recurse -Force $dst }
    if ($copyMode) {
      Copy-Item -Recurse -Force $src $dst
      Write-Utf8 (Join-Path $dst $SkillCopyMarker) 'Deployed by stack-init skills --copy. Managed: re-running replaces this directory; hand edits do not survive.'
      Remove-ExcludeLine $cgd $line
      Say "  $name copied (committable; re-run 'skills --copy $name' to refresh)"
    } else {
      try {
        New-Item -ItemType Junction -Path $dst -Target $src | Out-Null
        Add-ExcludeLine $cgd $line
        Say "  $name linked (junction) -> $src (machine-local; excluded from git)"
      } catch {
        # Junctions need the target on a local NTFS volume; a repo checkout on
        # a network share is the one setup that refuses. Copy still works.
        Warn "${name}: junction failed ($($_.Exception.Message)) - use: skills --copy $name"
        $fail = $true
      }
    }
  }
  Say 'skills load at session start - restart Claude Code to pick them up'
  if ($fail) { exit 1 }
}

# One aligned formatter for every verify line. The hand-spaced Write-Host pairs
# these replace spelled each label twice (once per branch) and had drifted to
# three different column widths, so adding a longer label silently misaligned a
# row. Same shape and widths as stack-init.sh's row helpers.
function Write-Row {
  param([string]$Label, [string]$Value)
  Write-Host ("  {0,-17} {1}" -f "${Label}:", $Value)
}
function Write-RowHave {
  param([string]$Cmd, [string]$Label, [string]$Ok, [string]$Missing)
  if (Have $Cmd) { Write-Row $Label $Ok } else { Write-Row $Label $Missing }
}
function Write-RowSkill {
  param([string]$Name)
  if (Test-Path (Join-Path $ClaudeDir "skills\$Name\SKILL.md")) { Write-Row "$Name skill" 'OK (global)' }
  else { Write-Row "$Name skill" 'NOT deployed - rerun global' }
}
function Write-RowHook {
  param([string]$Name, [string]$Label)
  # A SessionStart hook counts as wired only when BOTH the script exists and
  # settings.json references it - either half alone is a half-install.
  if ((Test-Path (Join-Path $ClaudeDir "hooks\$Name.ps1")) -and (Test-Path $SettingsPath) -and
      (Select-String -Path $SettingsPath -Pattern $Name -Quiet)) { Write-Row $Label 'OK (SessionStart)' }
  else { Write-Row $Label 'NOT registered' }
}

function Invoke-Verify {
  Say "verifying"
  $mcpOut = (claude mcp list 2>$null | Out-String)
  if ($mcpOut -match 'serena') { Write-Row 'serena (mcp)' 'OK (user scope)' }
  else { Write-Row 'serena (mcp)' 'NOT registered' }
  # Registered-but-disabled is the INTENDED state (D53), so it reports OK and the
  # enabled case is what gets flagged - the opposite of every other row here.
  $serenaRow = (($mcpOut -split "`r?`n") | Where-Object { $_ -match 'serena' }) -join ' '
  if ($serenaRow -match '(?i)disabled') { Write-Row 'serena state' 'OK (disabled by default - /mcp to enable per session)' }
  else { Write-Row 'serena state' 'ENABLED globally - D53 expects it off' }
  if ((claude plugin list 2>$null | Out-String) -match '(?i)ponytail') { Write-Row 'ponytail' 'OK (plugin installed)' }
  else { Write-Row 'ponytail' 'NOT installed - run: claude plugin install ponytail@ponytail' }
  # Serena retention gate (D57). serena/tools/tools_base.py logs
  # "<tool>: {params}; session_id: <id>" on every execution, so the "; session_id:"
  # suffix separates a REAL call from a startup manifest line. Reported on every
  # verify so the gate collects itself (the defect that sank D20).
  $serenaLogs = Join-Path $env:USERPROFILE '.serena\logs'
  if (Test-Path $serenaLogs) {
    $sact = @(Get-ChildItem -Path $serenaLogs -Recurse -File -ErrorAction SilentlyContinue |
      Where-Object { Select-String -Path $_.FullName -Pattern 'activate_project: .*session_id:' -Quiet }).Count
    if ($sact -gt 0) { Write-Row 'serena used' "OK ($sact session(s) activated it - D57 gate satisfied)" }
    else { Write-Row 'serena used' 'NEVER activated - if still 0 after ~10 sessions, remove it (D57, B7)' }
  }
  # ponytail's hooks are Node; without node the activation goes quiet rather than
  # erroring, so a broken install is invisible from inside a session.
  Write-RowHave 'node' 'node' 'OK (ponytail hooks)' 'MISSING - ponytail activation stays silent'
  Write-RowHook 'serena-autoinit' 'serena autoinit'
  Write-RowHook 'contract-refresh' 'contract refresh'
  if (Find-WtBin) { Write-Row 'worktrunk' 'OK (workflow tool - outside the contract)' }
  else { Write-Row 'worktrunk' 'NOT installed (optional)' }
  Write-RowHave 'opensrc' 'opensrc' 'OK (context tool - outside the contract)' 'NOT installed (optional)'
  Write-RowSkill 'opensrc'
  Write-RowSkill 'worktrunk'
  Write-RowSkill 'gauntlet-loop'
  if ((Test-Path $ClaudeMd) -and (Select-String -Path $ClaudeMd -Pattern 'claude-context-stack' -Quiet)) { Write-Row 'contract' "OK ($ClaudeMd)" }
  else { Write-Row 'contract' 'MISSING' }
  if (Test-InGitRepo) {
    # Everything below is PER CHECKOUT, and a linked worktree is a checkout like
    # any other: it gets its own Serena project, because that describes the code
    # at THIS path.
    $gd  = git rev-parse --git-dir 2>$null
    $cgd = git rev-parse --git-common-dir 2>$null
    if (-not $cgd) { $cgd = $gd }
    $isLinked = $false
    if ($gd -and $cgd) {
      if (-not [IO.Path]::IsPathRooted($gd))  { $gd  = Join-Path $PWD.Path $gd }
      if (-not [IO.Path]::IsPathRooted($cgd)) { $cgd = Join-Path $PWD.Path $cgd }
      $isLinked = ([IO.Path]::GetFullPath($gd) -ne [IO.Path]::GetFullPath($cgd))
    }
    if ($isLinked) {
      $br = git rev-parse --abbrev-ref HEAD 2>$null
      Write-Row 'checkout' "linked worktree ($br) - own Serena project"
    } else { Write-Row 'checkout' 'primary' }
    # Anchor on the repo ROOT, never cwd. .serena/ is written at the top level by
    # the SessionStart hook (which `cd $top` first), so cwd-relative tests
    # reported "none" for a fully wired repo whenever verify ran from a
    # subdirectory - and the README tells Windows users to run this script from
    # the repo's config\ directory, so that was the DEFAULT experience.
    $top = git rev-parse --show-toplevel 2>$null
    if (-not $top) { $top = (Get-Location).Path }
    $serenaYml = Join-Path $top '.serena/project.yml'
    if (Test-Path $serenaYml) { Write-Row 'serena project' 'OK (.serena\project.yml)' }
    else { Write-Row 'serena project' 'none - autoinits next session' }
    # Repo-local skills deployed by `skills` (or by hand - anything with a
    # SKILL.md counts, annotated by how it got here).
    $repoSkills = @()
    foreach ($sd in (Get-ChildItem -Path (Join-Path $top '.claude\skills') -Directory -Force -ErrorAction SilentlyContinue)) {
      if (-not (Test-Path (Join-Path $sd.FullName 'SKILL.md'))) { continue }
      if ($sd.Attributes -band [IO.FileAttributes]::ReparsePoint) { $repoSkills += "$($sd.Name)(link)" }
      else { $repoSkills += "$($sd.Name)(copy)" }
    }
    if ($repoSkills.Count) { Write-Row 'repo skills' ($repoSkills -join ' ') }
    else { Write-Row 'repo skills' 'none (optional - deploy: .\stack-init.ps1 skills <name>)' }
    # 3.0 installs NO git hooks: the four graph-refresh hooks went with graphify
    # (D52). Report any the stack left behind so an upgraded machine can be
    # cleaned, rather than silently leaving dead hooks in every repo.
    $hooksDir = Get-GitHooksDir
    if (-not $hooksDir) { $hooksDir = Join-Path $PWD.Path '.git\hooks' }
    $stale = @()
    foreach ($hook in 'post-commit', 'post-checkout', 'post-merge', 'post-rewrite') {
      $hookPath = Join-Path $hooksDir $hook
      if ((Test-Path $hookPath) -and (Select-String -Path $hookPath -Pattern 'claude-context-stack:' -Quiet)) { $stale += $hook }
    }
    if ($stale.Count) { Write-Row 'stale hooks' ("pre-3.0 graph hooks present: " + ($stale -join ' ') + " (safe to delete)") }
    else { Write-Row 'git hooks' 'OK (none - 3.0 installs no git hooks)' }
  }
}

$Usage = "usage: .\stack-init.ps1 [global|init|skills [--copy] [<name>...]|verify|contract [--condensed]|stats|help]"

# Anything the binder could not place lands in $Rest, INCLUDING dash-prefixed
# words that match no parameter. That made `.\stack-init.ps1 --help` leave
# $Command at its 'global' default and perform a full unattended install - the
# single most surprising thing this script could do to someone asking for help.
# Recognise help explicitly, and refuse to run `global` with leftover arguments
# rather than silently ignoring a typo'd command.
$HelpWords = @('help', '-h', '--help', '-help', '/?', '-?')
if (($HelpWords -contains $Command.ToLower()) -or ($Rest | Where-Object { $HelpWords -contains $_.ToLower() })) {
  Write-Output $Usage
  Write-Output ""
  Write-Output "  global    install the whole stack for this user (run once)"
  Write-Output "  skills    list the repo's skills, or junction/copy them into THIS repo's .claude\skills"
  Write-Output "  verify    report what is and is not wired up"
  Write-Output "  contract  print the routing contract (--condensed for the agent form)"
  exit 0
}

switch ($Command.ToLower()) {
  { $_ -in '', 'global' } {
    if ($Rest.Count) { Err "unexpected argument(s): $($Rest -join ' ')"; Write-Host $Usage; exit 1 }
    Install-Global
  }
  'skills'   { Deploy-RepoSkills $Rest }
  'verify'   {
    # --docs validates THIS REPO's documentation, not an installation, and is
    # deliberately Unix-only (the decisions log records why). Say so rather than
    # silently running the install check and reporting success for a flag that
    # did nothing.
    if (($Rest -contains '--docs') -or ($Rest -contains '-docs')) {
      Err "verify --docs is Unix-only by design - run: bash stack-init.sh verify --docs"
      exit 1
    }
    Invoke-Verify
  }
  'contract' {
    $file = if (($Rest -contains '--condensed') -or ($Rest -contains '-condensed')) { 'contract-condensed.md' } else { 'contract.md' }
    Write-Output (Get-Contract $file)
  }
  default    { Err "unknown command: $Command"; Write-Host $Usage; exit 1 }
}
# A stray $LASTEXITCODE from any native command above (pip/npm/winget/claude)
# must not become this script's exit code - completing the switch means success.
exit 0

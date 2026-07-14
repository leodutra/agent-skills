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
    Global (once): RTK hook, Serena at user scope (auto-activates per repo),
      graphify install, Headroom install, routing contract in
      $env:USERPROFILE\.claude\CLAUDE.md.
    Per-repo (one command): the graph derives from a specific codebase, so
      `stack-init.ps1 init` builds it and installs a local post-commit hook.

  USAGE
    .\stack-init.ps1            # or: global   -> global install (once)
    .\stack-init.ps1 init       # inside a repo -> build graph + hook
    .\stack-init.ps1 verify     # check wiring
    .\stack-init.ps1 contract   # print the routing contract

  AFTER GLOBAL INSTALL: start sessions with `headroom wrap claude`, not a bare
  `claude`, or Headroom's compression never engages (RTK/Serena/graphify are
  unaffected either way - they wire into the session, not the launch command).

  PREREQS: cargo, pip, uv, claude (Claude Code CLI), Git for Windows (its bash
  runs the post-commit hook). A language server per language. First run may need
  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned (or -ExecutionPolicy Bypass).
=============================================================================
#>
param([string]$Command = 'global')
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
   IF absent -> orient normally, and suggest running the stack init in this repo.
2. Specific symbols (definitions, references, implementations, file overviews)
   -> Serena (find_symbol, find_referencing_symbols, get_symbols_overview).
   Never grep for symbol names.
3. Compile / type / lint state -> Serena get_diagnostics_for_file.
   Do not run a full type-check just to read diagnostics Serena already provides.
4. Edits to existing symbols -> Serena symbol-level edits (replace_symbol_body,
   insert_after_symbol, rename_symbol), not string/regex replacement.
5. Anything that executes (tests, builds, git, tooling) -> Bash. RTK compresses it.
   Do NOT route execution through any MCP shell tool - that bypasses RTK.
6. The graph reflects the LAST COMMIT. For uncommitted work, use Serena (live).

## Source-of-truth precedence (on conflict)
code/LSP (Serena)  >  graph (graphify)
The LSP is live ground truth; the graph is a derivation that can trail the working
tree. On conflict, trust the LSP and rebuild the graph (`graphify update .`).
# <<< claude-context-stack <<<
'@

function Check-Deps {
  $miss = $false
  foreach ($d in 'git','claude') { if (-not (Have $d)) { Err "missing required: $d"; $miss = $true } }
  if (-not (Have 'cargo')) { Warn "cargo not found - needed to install RTK" }
  if (-not (Have 'pip'))   { Warn "pip not found - needed to install graphify" }
  if ($miss) { Err "install the required tools above, then re-run"; exit 1 }
}

function Install-Uv {
  if (Have 'uv') { return }
  Say "  installing uv (needed to run Serena)"
  if (Have 'winget') { winget install --id astral-sh.uv -e --silent }
  else { powershell -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex" }
  if (-not (Have 'uv')) { Warn "uv install failed - Serena will not be able to launch" }
}

function Install-Global {
  Check-Deps
  Say "RTK - output compression (global Bash hook)"
  if (Have 'rtk') { Say "  rtk present ($(rtk --version 2>$null))" }
  else { Say "  installing rtk"; cargo install --git https://github.com/rtk-ai/rtk }
  rtk init -g; Say "  rtk init -g (PreToolUse Bash hook registered)"

  Say "Serena - LSP symbols over MCP (user scope, auto-activates per repo)"
  if ((claude mcp list 2>$null | Select-String -Quiet 'serena')) {
    Say "  serena already registered - skipped"
  } else {
    Install-Uv
    claude mcp add --scope user serena -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context ide-assistant
    Say "  serena registered at user scope (ide-assistant: no shell/read tools)"
  }

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

  Say "Headroom - proxy-layer compression (final pass before the API)"
  if (Have 'headroom') { Say "  headroom present ($(headroom --version 2>$null))" }
  else {
    Say "  installing headroom (PyPI package: headroom-ai)"
    if (Have 'uv') { uv tool install 'headroom-ai[all]' } else { pip install 'headroom-ai[all]' }
  }
  Say "  installed - launch sessions with 'headroom wrap claude', not bare 'claude'"
  Say "  (not aliasing 'claude' here: a shell function/alias named 'claude' may"
  Say "  recurse into itself when headroom resolves the target binary - opt in"
  Say "  yourself once you've confirmed it's safe on your shell)"
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

  Say "Routing contract -> $ClaudeMd"
  New-Item -ItemType Directory -Force -Path $ClaudeDir | Out-Null
  $existing = if (Test-Path $ClaudeMd) { Get-Content -Raw $ClaudeMd } else { '' }
  $stripped = [regex]::Replace($existing,
    '(?s)# >>> claude-context-stack >>>.*?# <<< claude-context-stack <<<\r?\n?', '')
  $out = ($stripped.TrimEnd() + "`r`n`r`n" + $Contract).TrimStart()
  Set-Content -Path $ClaudeMd -Value $out -Encoding utf8
  Say "  contract written (idempotent - re-running replaces the managed block)"

  if (-not (Have 'rust-analyzer')) { Warn "rust-analyzer not on PATH - Serena needs it for Rust (rustup component add rust-analyzer)" }
  Write-Host ""; Say "Global install done. In each repo, run:  .\stack-init.ps1 init"
}

function Init-Project {
  if (-not (Test-Path .git -PathType Container)) { Err "run from a git repo root (no .git here)"; exit 1 }
  if (-not (Have 'graphify')) { Err "graphify not installed - run '.\stack-init.ps1 global' first"; exit 1 }
  Say "building knowledge graph (graphify .)"; graphify .
  Say "installing local post-commit hook (incremental rebuild)"; graphify hook install
  if (-not ((Test-Path .gitignore) -and (Select-String -Path .gitignore -Pattern '^graphify-out/' -Quiet))) {
    Add-Content -Path .gitignore -Value "`r`n# Claude context-stack knowledge graph`r`ngraphify-out/" -Encoding utf8
    Say "gitignored graphify-out/"
  }
  Write-Host ""; Say "Repo ready. First Claude session: let Serena onboard, then ask one"
  Say "architecture question and confirm it reads the graph instead of grepping."
}

function Invoke-Verify {
  Say "verifying"
  if (Have 'rtk') { Write-Host "  rtk:            OK ($(rtk --version 2>$null))" } else { Write-Host "  rtk:            NOT ON PATH" }
  if ((claude mcp list 2>$null | Select-String -Quiet 'serena')) { Write-Host "  serena (mcp):   OK (user scope)" } else { Write-Host "  serena (mcp):   NOT registered" }
  if (Have 'graphify') { Write-Host "  graphify:       OK" } else { Write-Host "  graphify:       NOT installed" }
  if (Have 'headroom') { Write-Host "  headroom:       OK (remember: launch via 'headroom wrap claude')" } else { Write-Host "  headroom:       NOT installed" }
  $wtFound = (Have 'git-wt') -or (Test-Path (Join-Path $env:USERPROFILE '.cargo\bin\wt.exe')) -or
    [bool](Get-ChildItem (Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Packages') -Directory -Filter 'max-sixty.worktrunk_*' -ErrorAction SilentlyContinue)
  if ($wtFound) { Write-Host "  worktrunk:      OK (workflow tool - outside the contract)" } else { Write-Host "  worktrunk:      NOT installed (optional)" }
  if (Have 'opensrc') { Write-Host "  opensrc:        OK (context tool - outside the contract)" } else { Write-Host "  opensrc:        NOT installed (optional)" }
  if ((Test-Path $ClaudeMd) -and (Select-String -Path $ClaudeMd -Pattern 'claude-context-stack' -Quiet)) { Write-Host "  contract:       OK ($ClaudeMd)" } else { Write-Host "  contract:       MISSING" }
  if (Test-Path .git -PathType Container) {
    if (Test-Path graphify-out\graph.json) { $kb = "{0:N0} KB" -f ((Get-Item graphify-out\graph.json).Length/1KB); Write-Host "  graph (here):   OK ($kb)" } else { Write-Host "  graph (here):   not built - run: .\stack-init.ps1 init" }
    if (Test-Path .git\hooks\post-commit) { Write-Host "  post-commit:    OK" } else { Write-Host "  post-commit:    none" }
  }
}

switch ($Command.ToLower()) {
  'global'   { Install-Global }
  ''         { Install-Global }
  'init'     { Init-Project }
  'verify'   { Invoke-Verify }
  'contract' { Write-Output $Contract }
  default    { Err "unknown command: $Command"; Write-Host "usage: .\stack-init.ps1 [global|init|verify|contract]"; exit 1 }
}
# A stray $LASTEXITCODE from any native command above (pip/npm/winget/claude)
# must not become this script's exit code - completing the switch means success.
exit 0

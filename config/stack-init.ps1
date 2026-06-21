#Requires -Version 5.1
<#
=============================================================================
  Claude Code Context Stack  -  global installer + per-repo init  (Windows)
=============================================================================

  WHAT THIS IS
  Three tools that cut the token cost of working in a real codebase with Claude
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

  PRINCIPLE: one question per layer.
    architecture/cross-module -> graphify  |  specific symbols -> Serena
    compile/type diagnostics  -> Serena    |  execute anything  -> Bash (RTK)
  PRECEDENCE on conflict: LSP (Serena, live) > graph (can be stale).

  GLOBAL vs PER-REPO
    Global (once): RTK hook, Serena at user scope (auto-activates per repo),
      graphify install, routing contract in $env:USERPROFILE\.claude\CLAUDE.md.
    Per-repo (one command): the graph derives from a specific codebase, so
      `stack-setup.ps1 init` builds it and installs a local post-commit hook.

  USAGE
    .\stack-setup.ps1            # or: global   -> global install (once)
    .\stack-setup.ps1 init       # inside a repo -> build graph + hook
    .\stack-setup.ps1 verify     # check wiring
    .\stack-setup.ps1 contract   # print the routing contract

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
# >>> claude-context-stack >>> (managed by stack-setup - edits here are overwritten)
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
  if (-not (Have 'uv'))    { Warn "uv not found - needed to run Serena" }
  if ($miss) { Err "install the required tools above, then re-run"; exit 1 }
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
    claude mcp add --scope user serena -- `
      uvx --from git+https://github.com/oraios/serena `
      serena start-mcp-server --context ide-assistant
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

  Say "Routing contract -> $ClaudeMd"
  New-Item -ItemType Directory -Force -Path $ClaudeDir | Out-Null
  $existing = if (Test-Path $ClaudeMd) { Get-Content -Raw $ClaudeMd } else { '' }
  $stripped = [regex]::Replace($existing,
    '(?s)# >>> claude-context-stack >>>.*?# <<< claude-context-stack <<<\r?\n?', '')
  $out = ($stripped.TrimEnd() + "`r`n`r`n" + $Contract).TrimStart()
  Set-Content -Path $ClaudeMd -Value $out -Encoding utf8
  Say "  contract written (idempotent - re-running replaces the managed block)"

  if (-not (Have 'rust-analyzer')) { Warn "rust-analyzer not on PATH - Serena needs it for Rust (rustup component add rust-analyzer)" }
  Write-Host ""; Say "Global install done. In each repo, run:  .\stack-setup.ps1 init"
}

function Init-Project {
  if (-not (Test-Path .git -PathType Container)) { Err "run from a git repo root (no .git here)"; exit 1 }
  if (-not (Have 'graphify')) { Err "graphify not installed - run '.\stack-setup.ps1 global' first"; exit 1 }
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
  if ((Test-Path $ClaudeMd) -and (Select-String -Path $ClaudeMd -Pattern 'claude-context-stack' -Quiet)) { Write-Host "  contract:       OK ($ClaudeMd)" } else { Write-Host "  contract:       MISSING" }
  if (Test-Path .git -PathType Container) {
    if (Test-Path graphify-out\graph.json) { $kb = "{0:N0} KB" -f ((Get-Item graphify-out\graph.json).Length/1KB); Write-Host "  graph (here):   OK ($kb)" } else { Write-Host "  graph (here):   not built - run: .\stack-setup.ps1 init" }
    if (Test-Path .git\hooks\post-commit) { Write-Host "  post-commit:    OK" } else { Write-Host "  post-commit:    none" }
  }
}

switch ($Command.ToLower()) {
  'global'   { Install-Global }
  ''         { Install-Global }
  'init'     { Init-Project }
  'verify'   { Invoke-Verify }
  'contract' { Write-Output $Contract }
  default    { Err "unknown command: $Command"; Write-Host "usage: .\stack-setup.ps1 [global|init|verify|contract]"; exit 1 }
}

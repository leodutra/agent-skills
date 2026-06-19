#Requires -Version 5.1
<#
  stack-init.ps1 — one-shot per-project bootstrap for the Claude Code context stack (Windows).
  PowerShell port of stack-init.sh. Prereqs (global, once): rtk init -g; serena registered
  at user scope; graphify install + graphify claude install; routing contract in
  $env:USERPROFILE\.claude\CLAUDE.md. Also requires Git for Windows (its bundled bash runs
  the post-commit hook graphify installs).
  Usage: run from the repo root. Idempotent — safe to re-run.
#>
$ErrorActionPreference = 'Stop'

if (-not (Test-Path .git -PathType Container)) {
  Write-Host "error: run from a git repo root" -ForegroundColor Red; exit 1
}
$PROJECT = Split-Path -Leaf (Get-Location)
function Say($m) { Write-Host "==> " -ForegroundColor Green -NoNewline; Write-Host $m }
function Write-Utf8($Path, $Text) { Set-Content -Path $Path -Value $Text -Encoding utf8 -NoNewline:$false }

# --- 1. Knowledge graph: build + keep fresh on commit ------------------------
Say "building knowledge graph (graphify .)"
graphify .
if ($LASTEXITCODE -ne 0) { Write-Host "error: graphify build failed" -ForegroundColor Red; exit 1 }

Say "installing git post-commit hook (incremental graph rebuild)"
graphify hook install

if (-not ((Test-Path .gitignore) -and (Select-String -Path .gitignore -Pattern '^graphify-out/' -Quiet))) {
  Add-Content -Path .gitignore -Value "`r`n# Knowledge graph outputs`r`ngraphify-out/" -Encoding utf8
  Say "gitignored graphify-out/"
}

# --- 2. Serena: project config (onboarding runs on first agent session) ------
if (-not (Test-Path .serena\project.yml)) {
  New-Item -ItemType Directory -Force -Path .serena | Out-Null
  Write-Utf8 ".serena\project.yml" @'
read_only: false
ignored_paths:
  - graphify-out
  - target
  - node_modules
  - dist
'@
  Say "wrote .serena\project.yml (Serena will onboard on first session)"
} else {
  Say ".serena\project.yml exists - skipped"
}

# --- 3. Docs layer scaffold (only files that don't exist yet) ----------------
New-Item -ItemType Directory -Force -Path docs\adr, docs\spec | Out-Null

if (-not (Test-Path SPEC.md)) {
  Write-Utf8 "SPEC.md" @"
# $PROJECT - Specification index

> SPEC.md is an INDEX, not a document. Deep sections live in docs/spec/,
> pulled on demand. Tag every section: [INVARIANT] | [AS-BUILT] | [PROPOSED].

## Statement
One paragraph: what this is and for whom.

## Invariants [INVARIANT]
Machine-checkable rules only (phrased so a lint/fitness function can verify):
- (none yet)

## Section index
| When touching... | Read |
|---|---|
| (area) | docs/spec/(file).md, ADR-NNN |

## Non-goals
- (explicitly out of scope)

## Open decisions
- (unsettled - do NOT assume an answer exists)
"@
  Say "scaffolded SPEC.md"
}

if (-not (Test-Path docs\adr\INDEX.md)) {
  Write-Utf8 "docs\adr\INDEX.md" @'
# ADR index
| ID | Title | Status |
|---|---|---|
'@
  Say "scaffolded docs\adr\INDEX.md"
}

if (-not (Test-Path docs\worklog.md)) {
  Write-Utf8 "docs\worklog.md" @"
# Worklog - $PROJECT
<!-- newest first; per session: Done / Rejected (with reason) / In flight -->
"@
  Say "scaffolded docs\worklog.md"
}

if (-not (Test-Path ROADMAP.md)) {
  Write-Utf8 "ROADMAP.md" @"
# Roadmap - $PROJECT

## Now

## Next

## Later
"@
  Say "scaffolded ROADMAP.md"
}

# --- 4. Thin project CLAUDE.md (global one carries the routing contract) -----
if (-not (Test-Path CLAUDE.md)) {
  Write-Utf8 "CLAUDE.md" @'
# Project context
Global routing contract applies (~/.claude/CLAUDE.md). Project specifics:
- Spec index: SPEC.md (pull deep sections from docs/spec/ on demand)
- Decisions: docs/adr/INDEX.md   - Continuity: docs/worklog.md
- Conventions: .claude/skills/ (if present)
'@
  Say "wrote thin project CLAUDE.md"
}

# --- 5. Verify ----------------------------------------------------------------
Say "verifying"
if (Test-Path graphify-out\graph.json) {
  $kb = "{0:N0} KB" -f ((Get-Item graphify-out\graph.json).Length / 1KB)
  Write-Host "  graph:        OK ($kb)"
}
if (Test-Path .git\hooks\post-commit) { Write-Host "  post-commit:  OK" }
else { Write-Host "  post-commit:  MISSING - rerun: graphify hook install" }
if (Get-Command rtk -ErrorAction SilentlyContinue) {
  Write-Host "  rtk:          OK ($(rtk --version 2>$null))"
} else { Write-Host "  rtk:          NOT ON PATH" }
if ((claude mcp list 2>$null | Select-String -Quiet -Pattern 'serena')) {
  Write-Host "  serena (mcp): OK"
} else { Write-Host "  serena (mcp): not registered at user scope" }

Say "done. First session in this repo: let Serena finish onboarding, then ask one architecture question to confirm graph-first routing."

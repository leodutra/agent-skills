#!/usr/bin/env bash
# stack-init — one-shot per-project bootstrap for the Claude Code context stack.
# Prereqs (global, once): rtk init -g; serena registered at user scope;
# graphify install + graphify claude install; routing contract in ~/.claude/CLAUDE.md.
# Usage: run from the repo root. Idempotent — safe to re-run.
set -euo pipefail

[ -d .git ] || { echo "error: run from a git repo root"; exit 1; }
PROJECT="$(basename "$PWD")"
say() { printf '\033[1;32m==>\033[0m %s\n' "$*"; }

# --- 1. Knowledge graph: build + keep fresh on commit ------------------------
say "building knowledge graph (graphify .)"
graphify .

say "installing git post-commit hook (incremental graph rebuild)"
graphify hook install

grep -q '^graphify-out/' .gitignore 2>/dev/null || {
  printf '\n# Knowledge graph outputs\ngraphify-out/\n' >> .gitignore
  say "gitignored graphify-out/"
}

# --- 2. Serena: project config (onboarding runs on first agent session) ------
if [ ! -f .serena/project.yml ]; then
  mkdir -p .serena
  cat > .serena/project.yml <<'YAML'
read_only: false
ignored_paths:
  - graphify-out
  - target
  - node_modules
  - dist
YAML
  say "wrote .serena/project.yml (Serena will onboard on first session)"
else
  say ".serena/project.yml exists — skipped"
fi

# --- 3. Docs layer scaffold (only files that don't exist yet) ----------------
mkdir -p docs/adr docs/spec

if [ ! -f SPEC.md ]; then
  cat > SPEC.md <<EOF
# ${PROJECT} — Specification index

> SPEC.md is an INDEX, not a document. Deep sections live in docs/spec/,
> pulled on demand. Tag every section: [INVARIANT] | [AS-BUILT] | [PROPOSED].

## Statement
One paragraph: what this is and for whom.

## Invariants [INVARIANT]
Machine-checkable rules only (phrased so a lint/fitness function can verify):
- (none yet)

## Section index
| When touching… | Read |
|---|---|
| (area) | docs/spec/(file).md, ADR-NNN |

## Non-goals
- (explicitly out of scope)

## Open decisions
- (unsettled — do NOT assume an answer exists)
EOF
  say "scaffolded SPEC.md"
fi

if [ ! -f docs/adr/INDEX.md ]; then
  cat > docs/adr/INDEX.md <<'EOF'
# ADR index
| ID | Title | Status |
|---|---|---|
EOF
  say "scaffolded docs/adr/INDEX.md"
fi

if [ ! -f docs/worklog.md ]; then
  cat > docs/worklog.md <<EOF
# Worklog — ${PROJECT}
<!-- newest first; per session: Done / Rejected (with reason) / In flight -->
EOF
  say "scaffolded docs/worklog.md"
fi

[ -f ROADMAP.md ] || { printf '# Roadmap — %s\n\n## Now\n\n## Next\n\n## Later\n' "$PROJECT" > ROADMAP.md; say "scaffolded ROADMAP.md"; }

# --- 4. Thin project CLAUDE.md (global one carries the routing contract) -----
if [ ! -f CLAUDE.md ]; then
  cat > CLAUDE.md <<'EOF'
# Project context
Global routing contract applies (~/.claude/CLAUDE.md). Project specifics:
- Spec index: SPEC.md (pull deep sections from docs/spec/ on demand)
- Decisions: docs/adr/INDEX.md   - Continuity: docs/worklog.md
- Conventions: .claude/skills/ (if present)
EOF
  say "wrote thin project CLAUDE.md"
fi

# --- 5. Verify ----------------------------------------------------------------
say "verifying"
[ -f graphify-out/graph.json ] && echo "  graph:        OK ($(du -h graphify-out/graph.json | cut -f1))"
[ -x .git/hooks/post-commit ]  && echo "  post-commit:  OK" || echo "  post-commit:  MISSING — rerun: graphify hook install"
command -v rtk >/dev/null      && echo "  rtk:          OK ($(rtk --version 2>/dev/null))" || echo "  rtk:          NOT ON PATH"
claude mcp list 2>/dev/null | grep -qi serena && echo "  serena (mcp): OK" || echo "  serena (mcp): not registered at user scope"

say "done. First session in this repo: let Serena finish onboarding, then ask one architecture question to confirm graph-first routing."

# Claude Code Context Stack

A pre-configured context-engineering setup for Claude Code: **graphify** (codebase knowledge graph), **Serena** (LSP symbol tools via MCP), **RTK** (CLI output compression), and a lightweight **docs layer** (spec / ADRs / worklog). Install the global layer once; bootstrap each repo with a single command. Every project then gets identical routing behavior — graph for architecture, LSP for symbols, compressed Bash for execution, docs for intent.

## Files

| File | What it is | When to read/run |
|---|---|---|
| `claude-code-context-stack.md` | The spec. Component roles and boundaries (§2), agent routing matrix (§3), per-component setup reference (§4), source-of-truth precedence (§5), docs-layer structure (§6), failure modes (§7), verification (§8), decision log (§9), global operating model (§10). | Read §1–3 and §10 first; §4–9 are reference. |
| `stack-init.sh` | The per-project bootstrap (Unix/macOS). Idempotent — builds the graph, installs the post-commit rebuild hook, writes Serena project config, scaffolds the docs layer, verifies. | Run once from each repo root, after the global install. |
| `stack-init.ps1` | The same bootstrap, ported to PowerShell for Windows. Step-for-step identical and equally idempotent (doc §10.6). | Run once per repo on Windows. |

## Quick start

```bash
# 1. Global layer — once, ever (full commands and rationale: doc §10.2)
#    rtk init -g · Serena at user scope · graphify global install
#    · language servers · routing contract → ~/.claude/CLAUDE.md

# 2. Make the bootstrap available everywhere
install -m 755 stack-init.sh ~/.local/bin/stack-init        # Unix/macOS
#   Windows: copy stack-init.ps1 to a dir on $env:PATH

# 3. Per repo — once
cd /path/to/project && stack-init                           # Unix/macOS
#   Windows (from repo root): stack-init.ps1
```

On Windows use PowerShell (`stack-init.ps1`), not cmd — see doc §10.6 for why, plus path translations and the optional `.bat` wrapper.

First session in a freshly bootstrapped repo: let Serena finish onboarding, then ask one architecture question and confirm the agent reads the graph instead of grepping.

## The one-line model

| Layer | Owns | Never used for |
|---|---|---|
| graphify | orientation, cross-module structure, blast radius | symbol lookup |
| Serena | symbol definitions/references, diagnostics, symbol-level edits | running anything |
| RTK | compressing Bash output (invisible) | prose/spec compression |
| Docs layer | intent — why, decisions, session continuity | describing code (code is ground truth) |

On conflict: **LSP > graph > spec > memories** — the spec is intent, the code is fact; divergence gets flagged, never silently reconciled (doc §5).

## Prerequisites

Arch Linux (adaptable), Claude Code, `cargo`, `uv`, `pip`, and a language server per language used (rust-analyzer / typescript-language-server / pyright). On Windows: PowerShell 5.1+ and Git for Windows (its bundled bash runs the post-commit hook).

## Versioning

Doc is at **v1.2** (changelog in its header). The doc is the source of truth for *why*; `stack-init.sh` (Unix) and `stack-init.ps1` (Windows) are the canonical executables for the per-project steps and are kept behaviorally identical — change behavior in the scripts, record the reasoning in the doc.

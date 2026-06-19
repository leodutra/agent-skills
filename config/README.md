# Claude Code Context Stack

A pre-configured setup for Claude Code that cuts the token cost of working in a real codebase, using three tools and the routing rules that make Claude use each for the one thing it's best at: **graphify** (codebase knowledge graph — structure), **Serena** (LSP symbol tools via MCP — symbols), **RTK** (CLI output compression). Install the global layer once; initialize each repo with a single command. Every project then gets identical routing behavior — graph for architecture, LSP for symbols, compressed Bash for execution.

No intent/docs layer: this stack is only the parts that move tokens, plus the global routing contract.

## Files

| File | What it is | When to read/run |
|---|---|---|
| `claude-code-context-stack.md` | The spec-of-whys. Component roles and boundaries (§2), agent routing matrix (§3), the routing contract (§4), source-of-truth precedence (§5), install & operating model (§6), failure modes (§7), decisions log (§8), verification (§9). | Read §1–3 first; the rest is reference. |
| `stack-setup.sh` | The installer (Linux/macOS). Self-documenting and self-installing. `global` mode wires the global layer; `init` builds a repo's graph + rebuild hook; also `verify` and `contract`. | `stack-setup` once globally, `stack-setup init` once per repo. |
| `stack-setup.ps1` | The same installer for Windows (PowerShell). Same modes, step-for-step parity, equally idempotent. | `.\stack-setup.ps1` global, then `init` per repo. |

The scripts are self-contained — the document is the deep reasoning, but you can run the stack from the scripts alone.

## Quick start

```bash
# 1. Global layer — once, ever
#    Installs RTK (Bash hook) + Serena (user scope) + graphify, and writes the
#    routing contract to ~/.claude/CLAUDE.md.
install -m 755 stack-setup.sh ~/.local/bin/stack-setup      # put it on PATH
stack-setup                                                 # = stack-setup global
#   Windows: copy stack-setup.ps1 to a dir on $env:PATH, then  .\stack-setup.ps1

# 2. Per repo — once (builds the graph + post-commit rebuild hook)
cd /path/to/project && stack-setup init                     # Unix/macOS
#   Windows (from repo root): .\stack-setup.ps1 init

# 3. Check the wiring any time
stack-setup verify
```

On Windows use PowerShell (`stack-setup.ps1`), not cmd — see doc §6.4 for path translations, the Git-for-Windows requirement, and the optional `.bat` wrapper.

First session in a freshly initialized repo: let Serena finish onboarding, then ask one architecture question and confirm the agent reads the graph instead of grepping. A repo where you haven't run `init` still works — the contract degrades gracefully.

## The one-line model

| Tool | Owns | Never used for |
|---|---|---|
| graphify | orientation, cross-module structure, blast radius | symbol lookup |
| Serena | symbol definitions/references, diagnostics, symbol-level edits | running anything |
| RTK | compressing Bash output (invisible) | prose/markdown compression |

On conflict: **LSP (Serena) > graph (graphify)** — the LSP is live ground truth; the graph is a derivation that can trail the working tree, so trust the LSP and rebuild the graph (doc §5).

## Prerequisites

Arch Linux (adaptable) or Windows, Claude Code, `git`, `cargo`, `uv`, `pip`, and a language server per language used (rust-analyzer / typescript-language-server / pyright). On Windows: PowerShell 5.1+ and Git for Windows (its bundled bash runs the post-commit hook).

## Versioning

Doc is at **v2.0** (changelog in its header). The doc is the source of truth for *why*; `stack-setup.sh` (Unix) and `stack-setup.ps1` (Windows) are the canonical executables and source of truth for behavior, kept behaviorally identical — change behavior in the scripts, record the reasoning in the doc.

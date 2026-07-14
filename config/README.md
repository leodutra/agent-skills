# Claude Code Context Stack

A pre-configured setup for Claude Code that cuts the token cost of working in a real codebase, using four tools and the routing rules that make Claude use each for the one thing it's best at: **graphify** (codebase knowledge graph — structure), **Serena** (LSP symbol tools via MCP — symbols), **RTK** (CLI output compression), **Headroom** (proxy-layer compression). Install the global layer once; initialize each repo with a single command. Every project then gets identical routing behavior — graph for architecture, LSP for symbols, compressed Bash for execution, compressed wire traffic for whatever's left.

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
#    Installs RTK (Bash hook) + Serena (user scope) + graphify + Headroom, and
#    writes the routing contract to ~/.claude/CLAUDE.md.
install -m 755 stack-setup.sh ~/.local/bin/stack-setup      # put it on PATH
stack-setup                                                 # = stack-setup global
#   Windows: copy stack-setup.ps1 to a dir on $env:PATH, then  .\stack-setup.ps1

# 2. Per repo — once (builds the graph + post-commit rebuild hook)
cd /path/to/project && stack-setup init                     # Unix/macOS
#   Windows (from repo root): .\stack-setup.ps1 init

# 3. Check the wiring any time
stack-setup verify

# 4. Every session after that — launch via Headroom's wrapper, not bare `claude`
headroom wrap claude
```

On Windows use PowerShell (`stack-setup.ps1`), not cmd — see doc §6.4 for path translations, the Git-for-Windows requirement, and the optional `.bat` wrapper.

First session in a freshly initialized repo: let Serena finish onboarding, then ask one architecture question and confirm the agent reads the graph instead of grepping. A repo where you haven't run `init` still works — the contract degrades gracefully.

## The one-line model

| Tool | Owns | Never used for |
|---|---|---|
| graphify | orientation, cross-module structure, blast radius | symbol lookup |
| Serena | symbol definitions/references, diagnostics, symbol-level edits | running anything |
| RTK | compressing Bash output (invisible) | prose/markdown compression |
| Headroom | compressing whatever still reaches the API — file dumps, history (invisible, requires `headroom wrap claude`) | replacing RTK, or building a second structure graph (`--code-graph` is never passed) |

On conflict: **LSP (Serena) > graph (graphify)** — the LSP is live ground truth; the graph is a derivation that can trail the working tree, so trust the LSP and rebuild the graph (doc §5).

## Extra tools (outside the contract)

The global installer also sets up two tools that are *not* part of the routing contract and never appear in it — the "only the parts that move tokens" claim above applies to the contract, not to what the installer ships. Both install non-fatally: their failure never blocks the stack.

**opensrc** (`npm install -g opensrc`) — fetches the exact installed version of any dependency's source (npm/PyPI/crates.io/GitHub; version auto-detected from the lockfile) into a global cache at `~/.opensrc/` and prints its path (`opensrc path zod`). It answers the one question the four tools can't: "what does this dependency actually do." Zero per-repo state — nothing gitignored, nothing per-worktree; the cache is shared by every checkout. Usage guidance lives in the [`opensrc` skill](../skills/opensrc/SKILL.md), not the contract.

**worktrunk** (`wt`; `git-wt` on Windows) — a git-worktree manager for parallel agents/tasks. It moves no tokens and routes no questions; it only manages where checkouts live.

Worktrees stay indistinguishable from any other checkout via one rule — *a worktree is a checkout; checkouts get init*. The installer writes a single user-global worktrunk `post-start` hook that re-runs the stack's per-checkout step (`graphify .` + rebuild hook) in every new worktree, only for repos whose primary checkout has `graphify-out/`. Un-inited repos are untouched; the contract degrades gracefully there exactly as it always did. RTK, Serena, and Headroom are global and need nothing per-worktree (Serena re-onboards per directory; that's inherent to worktrees).

One gotcha: `wt switch -x claude` launches bare `claude`, bypassing Headroom — use `wt switch -x 'headroom wrap claude'` (or launch the session yourself) to keep wire compression.

## Prerequisites

Arch Linux (adaptable) or Windows, Claude Code, `git`, `cargo`, `uv`, `pip`, and a language server per language used (rust-analyzer / typescript-language-server / pyright). On Windows: PowerShell 5.1+ and Git for Windows (its bundled bash runs the post-commit hook).

## Versioning

Doc is at **v2.1** (changelog in its header). The doc is the source of truth for *why*; `stack-setup.sh` (Unix) and `stack-setup.ps1` (Windows) are the canonical executables and source of truth for behavior, kept behaviorally identical — change behavior in the scripts, record the reasoning in the doc.

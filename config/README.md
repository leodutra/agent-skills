# Claude Code Context Stack

A pre-configured setup for Claude Code that cuts the token cost of working in a real codebase, using four tools and the routing rules that make Claude use each for the one thing it's best at: **graphify** (codebase knowledge graph — structure), **Serena** (LSP symbol tools via MCP — symbols), **RTK** (CLI output compression), **Headroom** (proxy-layer compression). Install the global layer once — that's the whole setup. A `claude` shim wraps every launch through Headroom, and the first session inside any git repo builds its graph in the background. Every project then gets identical routing behavior — graph for architecture, LSP for symbols, compressed Bash for execution, compressed wire traffic for whatever's left.

No intent/docs layer: this stack is only the parts that move tokens, plus the global routing contract.

## Files

| File | What it is | When to read/run |
|---|---|---|
| `claude-code-context-stack.md` | The spec-of-whys. Component roles and boundaries (§2), agent routing matrix (§3), the routing contract (§4), source-of-truth precedence (§5), install & operating model (§6), failure modes (§7), decisions log (§8), verification (§9). | Read §1–3 first; the rest is reference. |
| `stack-init.sh` | The installer (Linux/macOS). Self-documenting and self-installing. `global` mode wires the whole stack (including the claude shim and the graph-autobuild SessionStart hook); `init` builds a repo's graph eagerly; also `verify` and `contract`. | `stack-init` once, ever. `init` only for eager builds. |
| `stack-init.ps1` | The same installer for Windows (PowerShell). Same modes and behavior, equally idempotent (tool detection is platform-specific — e.g. worktrunk lookup probes winget paths on Windows). | `.\stack-init.ps1` once, ever. |

The scripts are self-contained — the document is the deep reasoning, but you can run the stack from the scripts alone.

## Quick start

```bash
# 1. Global layer — once, ever
#    Installs RTK (Bash hook) + Serena (user scope) + graphify + Headroom,
#    writes the routing contract to ~/.claude/CLAUDE.md, shadows bare `claude`
#    with a Headroom shim, and registers a SessionStart hook that autobuilds
#    each repo's graph on first session.
install -m 755 stack-init.sh ~/.local/bin/stack-init        # put it on PATH
stack-init                                                  # = stack-init global
#   Windows: copy stack-init.ps1 to a dir on $env:PATH, then  .\stack-init.ps1

# 2. Open a NEW shell (the shim's PATH entry has to load). That's it —
#    every `claude` launch is wrapped, every repo self-initializes.

# 3. Check the wiring any time
stack-init verify

# Optional: build a repo's graph eagerly instead of waiting for first session
#   (also does the tracked-file extras autobuild won't: .gitignore, .claude/agents)
cd /path/to/project && stack-init init
```

On Windows use PowerShell (`stack-init.ps1`), not cmd — see doc §6.4 for path translations and the Git-for-Windows requirement.

Escape hatches: `CLAUDE_NO_HEADROOM=1 claude` launches unwrapped once; `CLAUDE_STACK_NO_AUTOBUILD=1` or a `.graphify-skip` file in a repo root disables graph autobuild there. The first session in a repo with no graph gets a session-start note that a build is running; the contract degrades gracefully until it lands.

## The one-line model

| Tool | Owns | Never used for |
|---|---|---|
| graphify | orientation, cross-module structure, blast radius | symbol lookup |
| Serena | symbol definitions/references, diagnostics, symbol-level edits | running anything |
| RTK | compressing Bash output (invisible) | prose/markdown compression |
| Headroom | compressing whatever still reaches the API — file dumps, history (invisible; the claude shim wraps every launch automatically) | replacing RTK, or building a second structure graph (`--code-graph` is never passed) |

On conflict: **LSP (Serena) > graph (graphify)** — the LSP is live ground truth; the graph is a derivation that can trail the working tree, so trust the LSP and rebuild the graph (doc §5).

## Extra tools (outside the contract)

The global installer also sets up two tools that are *not* part of the routing contract and never appear in it — the "only the parts that move tokens" claim above applies to the contract, not to what the installer ships. Both install non-fatally: their failure never blocks the stack.

**opensrc** (`npm install -g opensrc`) — fetches the exact installed version of any dependency's source (npm/PyPI/crates.io/GitHub; version auto-detected from the lockfile) into a global cache at `~/.opensrc/` and prints its path (`opensrc path zod`). It answers the one question the four tools can't: "what does this dependency actually do." Zero per-repo state — nothing gitignored, nothing per-worktree; the cache is shared by every checkout. Usage guidance lives in the [`opensrc` skill](../skills/opensrc/SKILL.md), not the contract.

**worktrunk** (`wt`; `git-wt` on Windows) — a git-worktree manager for parallel agents/tasks. It moves no tokens and routes no questions; it only manages where checkouts live.

Worktrees stay indistinguishable from any other checkout via one rule — *a worktree is a checkout; checkouts get init*. The installer writes a single user-global worktrunk `post-start` hook that re-runs the stack's per-checkout step (`graphify .` + rebuild hook) in every new worktree, only for repos whose primary checkout has `graphify-out/`. Un-inited repos are untouched; the contract degrades gracefully there exactly as it always did. RTK, Serena, and Headroom are global and need nothing per-worktree (Serena re-onboards per directory; that's inherent to worktrees).

`wt switch -x claude` resolves `claude` on PATH like any shell, so it hits the shim and gets wrapped like every other launch. (Before the shim existed this was a bare-launch gotcha; it isn't anymore.)

## Prerequisites

Arch Linux (adaptable) or Windows, Claude Code, `git`, `cargo`, `uv`, `pip`, and a language server per language used (rust-analyzer / typescript-language-server / pyright). On Windows: PowerShell 5.1+ and Git for Windows (its bundled bash runs the post-commit hook).

## Versioning

Doc is at **v2.3** (changelog in its header). The doc is the source of truth for *why*; `stack-init.sh` (Unix) and `stack-init.ps1` (Windows) are the canonical executables and source of truth for behavior, kept behaviorally equivalent — change behavior in the scripts, record the reasoning in the doc.

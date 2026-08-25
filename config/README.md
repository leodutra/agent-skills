# Claude Code Context Stack

A pre-configured setup for Claude Code, built on one rule: **eliminate waste at its source, never compress downstream.** Two components — **Serena** (LSP symbol tools via MCP, *opt-in per session*) and **ponytail** (minimal-code discipline, default-on) — plus a global routing contract. Install the global layer once; that's the whole setup, and there is no per-repo step. 3.0 removed graphify, RTK, and Headroom: the stack no longer intercepts anything and holds no per-repo state (D51, D52).

No intent/docs layer: this stack is only the parts that move tokens, plus the global routing contract.

## Files

| File | What it is | When to read/run |
| --- | --- | --- |
| `claude-code-context-stack.md` | The spec: what the stack is and how to operate it. Component roles and boundaries (§2), agent routing matrix (§3), the routing contract (§4), source-of-truth precedence (§5), install & operating model (§6), failure modes (§7), verification (§8). Carries no rationale — only `D<n>` citations. | Read §1–3 first; the rest is reference. |
| `DECISIONS.md` | Every "why", as numbered append-only decisions (D1–D48). A decision's body is never rewritten: when one is reversed or its stated reason turns out to be wrong, a new entry is appended and the old one gets a pointer. | When you want to know why something is the way it is — or before changing it. |
| `CHANGELOG.md` | What changed and when, one terse line per change, each citing the decision it implements. | To see what moved between versions. |
| `BACKLOG.md` | Open defects in the decision set, one item each, ordered by cost. Carries no rationale — closing an item means appending a decision and deleting the item, so the file empties itself. | Before starting work on the stack, and when a decision looks wrong. |
| `stack-init.sh` | The installer (Linux/macOS). Self-documenting and self-installing. `global` mode wires the whole stack; `skills` deploys the repo's domain skills into the current repo's `.claude/skills/` (D48); also `verify`, `verify --docs` (checks this repo's own `§`/`D<n>` references — Unix-only, D42) and `contract`. | `stack-init` once, ever. `skills` per repo, as needed. |
| `stack-init.ps1` | The Windows installer (PowerShell). Same command surface and functional guarantees, equally idempotent; platform-native integrations differ where necessary. | `.\stack-init.ps1` once, ever. |
| `contract.md` / `contract-condensed.md` | The routing contract itself, as the installers write it: the full form into `~/.claude/CLAUDE.md`, the short form into every agent file. Both installers read these, so the two platforms cannot drift on the one artifact they both produce. ASCII-only — Windows PowerShell 5.1 decodes a BOM-less file as ANSI. | Edit here to change the contract; never edit the managed block in `CLAUDE.md`. |

Keep the scripts inside the repo (symlink onto PATH rather than copying) — they deploy the [`skills/`](../skills/) extras and read `contract*.md` repo-relative.

## Quick start

```bash
# 1. Global layer — once, ever
#    Registers Serena (user scope, left DISABLED), installs the ponytail
#    plugin, writes the routing contract to ~/.claude/CLAUDE.md, and registers
#    the serena-autoinit + contract-refresh SessionStart hooks.
ln -s "$PWD/stack-init.sh" ~/.local/bin/stack-init          # symlink onto PATH
#    (symlink, not copy — the script deploys skills/ from the repo next to it)
stack-init                                                  # = stack-init global
#   Windows: run  .\stack-init.ps1  from the repo's config\ directory

# 2. That's it — there is no per-repo step and no new shell needed.
#    Serena stays OFF until a session turns it on with /mcp (D53).

# 3. Check the wiring any time
stack-init verify

# Optional: give a repo one of this repo's DOMAIN skills (they are never
#   installed globally — every global skill's description costs every session
#   in every project, D48). Symlinked by default; --copy for a committable copy.
cd /path/to/project && stack-init skills architecture-blueprint
stack-init skills           # lists what's deployable and where each one is
```

On Windows use PowerShell (`stack-init.ps1`), not cmd — see doc §6.5 for path translations and the Git-for-Windows requirement.

Escape hatches: `CLAUDE_STACK_NO_SERENA_INIT=1` (or a `.serena-skip` file in a repo root) disables the Serena project autoinit there. Serena itself is off unless a session turns it on with `/mcp` — that is the normal state, not a misconfiguration (D53).

## The one-line model

| Tool | Owns | Never used for |
| --- | --- | --- |
| Serena *(opt-in)* | symbol definitions/references, diagnostics, symbol-level edits | running anything; sessions that don't need it |
| ponytail *(always on)* | minimal-code discipline, injected at session start | routing any question |

Two waste sources are deliberately **unowned**: orientation (graphify's old job) and tool-output noise (RTK's). Nothing compresses wire traffic either. Keeping output small is a routing choice now — prefer targeted commands over ones that dump (D51, D52).

Source of truth: the LSP when Serena is enabled. Nothing in the stack derives or caches a second model of the code, so there is no precedence conflict left to resolve (doc §5).

## Extra tools (outside the contract)

The global installer also sets up three extras that are *not* part of the routing contract and never appear in it — the "only the parts that move tokens" claim above applies to the contract, not to what the installer ships. Their installation is non-fatal: failure never blocks the stack.

For each, the installer also mirrors its whole skill directory from [`skills/<name>/`](../skills/) (SKILL.md plus any supporting files) to `~/.claude/skills/` — without that, the skill never surfaces globally. The repo copies are the canonical source and work as ordinary standalone skills in any setup; stack-init deploys them verbatim, repo-relative (which is why the script must run from — or be symlinked into — the checkout), and the deployed copies are fully managed: overwritten on every run, stale files removed. `verify` reports all three skills.

That global set is exactly three and does not grow: the repo's remaining skills (architecture-blueprint, rust-bevy-architecture, rust-wgpu-functional, macro-analyst) are **domain** skills, and every skill in `~/.claude/skills/` pays its description into every session's context in every project, relevant or not (D48). Deploy those per repo instead with `stack-init skills <name>` — a symlink on Unix, a junction on Windows (no Developer Mode needed), kept out of git via `.git/info/exclude`; `--copy` produces a committable copy for shared repos, marker-guarded so a refresh never touches a same-named skill this command didn't create. Bare `stack-init skills` lists what's deployable and where each one currently is; `verify` shows the current repo's deployments.

**gauntlet-loop** — turns a goal into a paste-ready prompt that makes a separate builder and harsh critic compare the work against a concrete reference until it wins. It has no external binary and is available as a standalone skill; stack-init only deploys its canonical copy.

**opensrc** (`npm install -g opensrc`) — fetches the exact installed version of any dependency's source (npm/PyPI/crates.io/GitHub; version auto-detected from the lockfile) into a global cache at `~/.opensrc/` and prints its path (`opensrc path zod`). It answers a question neither component covers: "what does this dependency actually do." Zero per-repo state — nothing gitignored, nothing per-worktree; the cache is shared by every checkout. Usage guidance lives in the [`opensrc` skill](../skills/opensrc/SKILL.md), not the contract.

**worktrunk** (`wt`; `git-wt` on Windows) — a git-worktree manager for parallel agents/tasks. It moves no tokens and routes no questions; it only manages where checkouts live. `git-wt` and `git wt` are the same binary, not two names to pick between — git auto-discovers any `git-<name>` executable on PATH and exposes it as a `git <name>` subcommand. The Windows/Linux split is deliberate, not an inconsistency to fix: stock Win11 ships Windows Terminal's own `wt.exe`, so `stack-init.ps1` never trusts bare `wt` as evidence of worktrunk and only accepts `git-wt` (winget's install name) or a `.cargo\bin\wt.exe` found by explicit path; Linux/macOS have no such collision — brew and cargo both name the binary plainly `wt` — so `stack-init.sh` keeps bare `wt` first, matching what's actually installed there.

Worktrees stay indistinguishable from any other checkout via one rule — *a worktree is a checkout; checkouts get init*. Serena is the only component with per-worktree state: a linked worktree is a separate checkout at its own path, so it gets its own `.serena/project.yml` (named `repo@branch`) from the serena-autoinit SessionStart hook — no manual step, but not "nothing" either (doc §6.3, D33).

## Prerequisites

Arch Linux (adaptable) or Windows, Claude Code, `git`, `cargo`, `uv`, `pip`, and a language server per language used (rust-analyzer / typescript-language-server / pyright). On Linux/macOS also `python3` — every `settings.json` merge goes through it. On Windows: PowerShell 5.1+ and Git for Windows (its bundled bash runs the post-commit hook).

## Versioning

Docs are at **v2.5** — see [`CHANGELOG.md`](CHANGELOG.md). `stack-init.sh` (Unix) and `stack-init.ps1` (Windows) are the canonical executables and the source of truth for *behavior*, kept functionally equivalent across their platform-native implementations. [`DECISIONS.md`](DECISIONS.md) is the source of truth for *why*. Change behavior in the scripts, record the reasoning as a new decision, add a changelog line.

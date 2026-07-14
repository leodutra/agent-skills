---
name: worktrunk
description: Manage Git worktrees with Worktrunk (`wt`) for parallel/isolated work — one worktree per branch, paths auto-generated, lifecycle automated. Use this skill whenever the user asks to work on something "in parallel", "in isolation", "without touching my current branch", to run multiple agents/tasks side by side, to create/switch/list/remove worktrees, to merge a worktree back, or anything mentioning `wt`, worktrunk, or `git worktree`. Also trigger for setting up worktrunk hooks (post-create/pre-merge/post-merge) or debugging its shell integration.
---

# Worktrunk

CLI wrapper around `git worktree` (binary: `wt`; **`git-wt` on Windows** — winget installs it under that name to avoid the Windows Terminal `wt` collision). Model: **one worktree per branch, addressed by branch name; paths are computed from a template, never typed.**

Prefer `wt` over raw `git worktree add/remove` whenever it is installed — it also runs the repo's configured hooks (dependency install, env files), which raw git skips.

## When to reach for a worktree at all

- User wants a second task going without disturbing uncommitted work in the current tree.
- User wants to review/try a branch or PR while keeping their session where it is.
- Running multiple long tasks side by side, each needing its own working directory.

Not for subagents spawned via the Agent tool — those already get isolation via `isolation: "worktree"`. Worktrunk is for worktrees the *user* (or this session) works in directly.

## Verify install (before first use in a session)

```bash
wt --version || git-wt --version
```

If missing, offer install (do not install unasked):
- Windows: `winget install max-sixty.worktrunk` then `git-wt config shell install`
- macOS/Linux: `brew install worktrunk && wt config shell install`
- Any platform: `cargo install worktrunk && wt config shell install`

`wt config shell install` enables auto-cd on switch (bash/zsh/fish/nushell/PowerShell). Without it, `wt switch` prints the path instead of changing directory — still usable from an agent: capture the path and run subsequent commands there.

## Core commands

| Task | Command |
|---|---|
| New worktree + branch | `wt switch -c <branch>` |
| Switch to existing | `wt switch <branch>` |
| Check out a PR in its own worktree | `wt switch pr:<number>` |
| New worktree and launch an agent in it | `wt switch -x claude -c <branch> -- '<task>'` |
| Status across all worktrees | `wt list` (add `--full` for CI status + summaries) |
| Merge worktree back into a branch | `wt merge <target>` (squash/rebase/merge + cleanup) |
| Delete current worktree + its branch | `wt remove` |
| Commit staged changes | `wt step commit` |
| Copy build caches into a fresh worktree | `wt step copy-ignored` |

`wt merge` finishes the whole lifecycle: it can generate the commit message, squash, rebase onto the target, merge, and remove the worktree. Prefer it over hand-rolling `git merge` + `git worktree remove` when the user wants a worktree "landed".

## Hooks

Configured per repo; run automatically on lifecycle events:

- `post-create` — after a worktree is created (typical: install deps, copy `.env`, `wt step copy-ignored` for build caches).
- `pre-merge` — before merging (typical: tests, lint — a failing hook blocks the merge).
- `post-merge` — after merging.

If a fresh worktree "doesn't build" or lacks env files, the fix is usually a `post-create` hook, not manual setup notes. Manage with `wt hook`.

## Interop with this environment

- Worktrees created by `wt` are ordinary git worktrees — all git tooling works inside them.
- On Windows, hooks execute via Git for Windows' bash; it must be installed.
- Each worktree shares the repo's object store: cheap to create, but a branch checked out in one worktree cannot be checked out in another (git rule, not a worktrunk one).
- If a `graphify` graph exists (Context Stack), it lives per checkout and reflects the last commit — a fresh worktree starts from its branch's last commit, so the graph is valid there after `stack-setup init`/`graphify update .` runs in that worktree.

## Failure modes

- `wt` not found on Windows → try `git-wt`; if the user wants the short name, an alias/shim is their call.
- `wt switch` doesn't change directory → shell integration not installed; run `wt config shell install`, or (as an agent) use the printed path directly.
- Merge blocked → a `pre-merge` hook failed; show its output and fix the underlying failure rather than bypassing the hook.

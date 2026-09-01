---
name: opensrc
description: Read the actual source code of a dependency instead of guessing from types, docs, or training data. Use this skill whenever behavior of a third-party package matters — "how does X work internally", "why does this library do Y", debugging an error whose stack trace points into a dependency, checking what a function really returns or throws, verifying an edge case the docs don't cover, or any time you are about to assert what an npm/PyPI/crates.io package does without having read it. Trigger on mentions of opensrc, reading node_modules/vendored source, or dependency internals.
---

# opensrc

CLI (Vercel Labs) that fetches the exact source of a dependency into a global cache and prints its path. Point of the tool: **never assert what a library does from memory — read the code at the version the project actually uses.**

```bash
opensrc path <pkg>        # fetch on first use, print absolute path to source
```

The version is auto-detected from the project's lockfile (`pnpm-lock.yaml`, `package-lock.json`, etc.) when not specified — so the source you read matches the installed version, not the latest.

## Identifiers

| Registry | Form |
| --- | --- |
| npm (default) | `opensrc path zod`, `opensrc path zod@3.22.0` |
| PyPI | `opensrc path pypi:requests` |
| crates.io | `opensrc path crates:serde` |
| GitHub/GitLab | `opensrc path owner/repo` or a full URL |

## Other commands

- `opensrc fetch <pkg>` — cache without printing the path (pre-warm, CI)
- `opensrc list [--json]` — what's cached
- `opensrc remove <pkg>` / `opensrc clean [--npm|--pypi|--crates]` — evict

## Where source lives

Global cache `~/.opensrc/` (override: `OPENSRC_HOME`), laid out as `repos/<host>/<owner>/<repo>/<ref>`. Nothing is written into the project — no gitignore entry, no per-repo init, and worktrees need nothing special (the cache is shared across all checkouts).

## Working with fetched source

- Capture the printed path, then Read/Grep *within that path*. The Context Stack's "never grep for symbols" rule applies to project code Serena indexes — a fetched dependency tree is outside the LSP project, so grep there is correct.
- Read the specific function/module in question, not the whole package. Fetching is cheap; dumping a library into context is not.
- opensrc does no signature verification or security auditing — it answers "what does this code do", not "is this package safe".

## When NOT to use

- The question is about the project's own code → Serena (when enabled) or native search per the routing contract.
- Public API shape is enough (signatures, option names) → types/docs already in the project answer it cheaper.

# agent-skills

Personal collection of Claude Code skills, reference docs, and configuration for AI-assisted development.

## Layout

| Path | What it is |
|---|---|
| `skills/` | Claude Code skills (`SKILL.md` + `references/`), auto-invoked by Claude Code based on their `description` frontmatter. |
| `docs/` | Standalone reference specs (not skills) that codify conventions for a stack. |
| `config/` | The Claude Code Context Stack — install scripts and spec for graphify, Serena, RTK, and Headroom. |
| `agents/` | Reserved for custom agent definitions. Currently empty. |

## Skills

| Skill | Use for |
|---|---|
| [`architecture-blueprint`](skills/architecture-blueprint/SKILL.md) | Domain-first backend/full-stack architecture: modular monoliths, vertical slices, type-driven domain modeling, ADRs. |
| [`macro-analyst`](skills/macro-analyst/SKILL.md) | Structured macro/FX analysis for currency pairs, rate differentials, central bank policy. |
| [`opensrc`](skills/opensrc/SKILL.md) | Read the actual source of a dependency (npm/PyPI/crates.io/GitHub) at the installed version via `opensrc path`, instead of guessing from types or docs. |
| [`rust-bevy-architecture`](skills/rust-bevy-architecture/SKILL.md) | Architecture method for Bevy (Rust ECS) game projects — layout, plugins, messages/observers, scheduling, determinism. |
| [`rust-wgpu-functional`](skills/rust-wgpu-functional/SKILL.md) | Idiomatic Rust for wgpu / bare-metal GPU code, applying functional principles without sacrificing performance. |
| [`worktrunk`](skills/worktrunk/SKILL.md) | Git worktree management via Worktrunk (`wt`) for parallel/isolated work — create, switch, merge, and clean up worktrees by branch name. |

Skills are picked up automatically by Claude Code when their trigger conditions match a request — no manual invocation needed beyond what each `SKILL.md` describes.

## Docs

- [`docs/RUST_BACKEND_STACK.md`](docs/RUST_BACKEND_STACK.md) — default technology and architectural choices for Rust backend systems.
- [`docs/RUST_IDIOMATIC_TYPE_DRIVEN_PATTERNS.md`](docs/RUST_IDIOMATIC_TYPE_DRIVEN_PATTERNS.md) — type-driven Rust patterns (newtypes, parse-don't-validate, illegal states unrepresentable).

## Config — Claude Code Context Stack

[`config/`](config/README.md) holds a separate, self-contained setup: four tools (graphify, Serena, RTK, Headroom) plus the routing contract that tells Claude which tool to use for structure, symbols, execution output, and wire-level compression. See `config/README.md` for quick start and `config/claude-code-context-stack.md` for the full spec.

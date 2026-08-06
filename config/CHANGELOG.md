# Changelog — Claude Code Context Stack

One line per change. The "why" lives in [`DECISIONS.md`](DECISIONS.md); entries
cite the decision they implement rather than restating it. Behavior is defined by
`stack-init.sh` / `stack-init.ps1` (D2) — this file records what moved and when.

Fix entries with no `D<n>` are defect repairs that changed no decision.

## 2.4

Backlog-clearing release: the six open defects in the decision set are closed,
four of them by declining or affirming rather than by building. Two gates that
could never fire are now decisions; one standing check that was circular is now
a number you can read off `/cost`; two install-time writes that went stale are
now self-healing.

- **Change** Serena tool-surface audit declined outright — it was gated on
  per-tool usage data nothing in the stack collects. [D39](DECISIONS.md#d39) (declines [D23](DECISIONS.md#d23))
- **Change** Headroom stays default-on despite being the unverified layer;
  recorded deliberately, with both alternatives evaluated and rejected. [D40](DECISIONS.md#d40) (affirms [D25](DECISIONS.md#d25))
- **Fix** the cache-bust symptom no longer requires a matched bare session to
  observe — it was defined in terms of the benchmark D37 declined, so nothing
  was being watched. Now a single-session ratio:
  `cache_read / (cache_read + cache_creation)` after ~10 turns. [D41](DECISIONS.md#d41)
- **Add** `stack-init verify --docs` — every `§` reference and every `D<n>`
  citation across the doc set must resolve. Unix-only by design. [D42](DECISIONS.md#d42) (corrects [D38](DECISIONS.md#d38))
- **Add** contract-refresh `SessionStart` hook: editing `contract-condensed.md`
  now propagates to `~/.claude/agents/*.md` without re-running the installer.
  Scoped to user-global files only — `.claude/agents/` is tracked, so it stays
  with `init` per [D24](DECISIONS.md#d24). [D43](DECISIONS.md#d43) (narrows [D19](DECISIONS.md#d19))
- **Fix** `--no-tokensave` is probed by the shim at launch and cached on
  headroom's version, instead of being baked in at install and going stale on
  the next upgrade — which silently restored the duplicate code graph
  [D13](DECISIONS.md#d13) forbids. [D44](DECISIONS.md#d44) (narrows [D26](DECISIONS.md#d26))
- **Add** `BACKLOG.md` recorded as the fourth document: open defects in the
  decision set, one item each, deleted as they close. [D45](DECISIONS.md#d45) (extends [D36](DECISIONS.md#d36))

## 2.3.3

Documentation-integrity release: three places where the spec contradicted the
shipped scripts, plus a hook that had been shipping undocumented.

- **Fix** Serena does *not* activate a project from the session's cwd — the claim
  the spec used to justify the bare user-scope registration. [D33](DECISIONS.md#d33) (corrects [D4](DECISIONS.md#d4))
- **Add** serena-autoinit `SessionStart` hook documented: per-checkout
  `.serena/project.yml`, non-destructive repair, activation instruction on every
  path. Shipped earlier, undocumented until now. [D33](DECISIONS.md#d33)
- **Add** Serena's language-server set derived from tracked files rather than
  Serena's own detection. [D34](DECISIONS.md#d34)
- **Fix** `graphify claude install`'s PreToolUse hook is active, not a no-op; the
  layer-bleed mitigation had been resting on the stale claim. [D35](DECISIONS.md#d35) (corrects [D5](DECISIONS.md#d5))
- **Fix** `headroom stats` → `headroom savings` in the cache-bust symptom and the
  benchmark procedure; the subcommand has never existed. [D29](DECISIONS.md#d29)
- **Add** failure mode "Serena registered but never activated (silent)".
- **Change** §2.4 boundary 5 no longer conditions Headroom on a benchmark nobody
  runs: retained on wire-token evidence, cache economics recorded as unverified,
  status provisional and monitored. [D37](DECISIONS.md#d37) (narrows [D20](DECISIONS.md#d20))
- **Change** spec split into spec / `DECISIONS.md` / `CHANGELOG.md`; enforced by
  review, not tooling. [D36](DECISIONS.md#d36), [D38](DECISIONS.md#d38)
- **Change** spec sections renumbered: Serena autoinit is §6.3; Windows §6.5;
  optional MCP server §6.6; verification §8.
- **Fix** `README.md` file table said the decisions log runs D1–D37; D38 exists.

## 2.3.2

Installer deduplication and non-fatal optional installs. No change to the layer
model or the contract.

- **Change** contract text reduced to one copy in `contract.md` /
  `contract-condensed.md`, read by both installers. [D30](DECISIONS.md#d30)
- **Change** this repo's git hooks reduced to one implementation; `init` delegates
  to the generated hook via `--hooks`/`-Hooks`. [D31](DECISIONS.md#d31)
- **Fix** POSIX installer no longer aborts the whole run on a missing optional
  dependency, which had been taking out the contract write. [D32](DECISIONS.md#d32)
- **Fix** `Find-WtBin` shared with `verify`, which had inlined a looser copy that
  accepted a winget package directory without `git-wt.exe` in it.
- **Fix** `verify` output goes through one aligned row formatter per platform,
  replacing hand-spaced pairs that had drifted to three column widths.

## 2.3.1

Installer defect fixes. No change to the layer model or the contract.

- **Fix** `settings.json` is never clobbered when it fails to parse. [D27](DECISIONS.md#d27)
- **Fix** repo state anchored on `git rev-parse --show-toplevel`, not cwd. [D28](DECISIONS.md#d28)
- **Fix** `stats` calls `headroom savings`, not the nonexistent `headroom stats`. [D29](DECISIONS.md#d29)
- **Fix** `stack-init.ps1 --help` no longer performs an unattended global install
  (PowerShell bound the unmatched flag into `ValueFromRemainingArguments`, leaving
  `$Command` at its `global` default); `global` now refuses stray arguments.
- **Fix** every native call in the Windows installer is `Have`-guarded — under
  `$ErrorActionPreference='Stop'` a missing executable aborted the run before the
  contract was written.
- **Fix** empty files no longer crash the contract writer (`Get-Content -Raw`
  returns `$null`, not `''`).
- **Fix** appending the contract to a file with no trailing newline no longer glues
  the marker onto the last line and re-appends the block forever.
- **Fix** `python3` declared a required dependency on POSIX, where every
  `settings.json` merge goes through it.

## 2.3

The two remaining manual steps automated.

- **Add** `SessionStart` graph-autobuild hook: per-repo init is no longer a step.
  [D24](DECISIONS.md#d24)
- **Add** recursion-safe `claude` shim in `~/.claude/stack-bin`; Headroom engages
  by default. [D25](DECISIONS.md#d25)
- **Remove** the 2.2 `clw`/`hclaude`/`claudew` wrapper as superseded; the installer
  deletes any it previously wrote. [D25](DECISIONS.md#d25)
- **Add** `--no-tokensave` probed at install time and passed, against upstream's
  new default-on tokensave graph. [D26](DECISIONS.md#d26)
- **Change** contract rule 1's absent-branch says the graph may be mid-autobuild
  instead of suggesting a manual init.

## 2.2

- **Fix** graph staleness model corrected to "last rebuild", not "last commit";
  rule 6 widened to allow an on-demand refresh. [D15](DECISIONS.md#d15)
- **Add** `post-checkout` / `post-merge` / `post-rewrite` refresh hooks alongside
  `post-commit`; worktree support documented. [D16](DECISIONS.md#d16)
- **Add** Headroom launcher wrapper plus a `SessionStart` hook that flags an
  unwrapped session. [D17](DECISIONS.md#d17)
- **Add** condensed contract propagated into `~/.claude/agents/` and
  `.claude/agents/`. [D19](DECISIONS.md#d19)
- **Add** cache-economics benchmark procedure gating Headroom's place in the
  stack. [D20](DECISIONS.md#d20)
- **Add** `stack-init stats` for dated rtk/headroom usage snapshots.
- **Defer** Serena tool-surface audit, gated on real usage data. [D23](DECISIONS.md#d23)

## 2.1.1

- **Change** installer name unified to `stack-init` everywhere; the docs had said
  `stack-setup` while the shipped files were already `stack-init.*`. No behavior
  change.

## 2.1

- **Add** Headroom as a fourth, proxy-layer tool. [D12](DECISIONS.md#d12)
- **Add** Serena launched from a pinned binary rather than `uvx --from git+…`,
  with migration of an existing uvx registration. [D11](DECISIONS.md#d11)
- **Change** `--code-graph` and `--memory` deliberately never passed. [D13](DECISIONS.md#d13)

## 2.0

- **Remove** the docs/intent layer (SPEC/ADR/worklog) and the per-project skill.
  [D1](DECISIONS.md#d1)
- **Change** install consolidated into a single self-documenting installer per OS.
  [D2](DECISIONS.md#d2)
- **Remove** `graphify claude install` from the global step. [D5](DECISIONS.md#d5)
- **Change** Serena registered at user scope, in the `claude-code` context with
  shell/read/search disabled. [D3](DECISIONS.md#d3), [D4](DECISIONS.md#d4)

## 1.x

- Five-layer model with a docs layer and a `stack-init` bootstrap — a name
  coincidence with the current installer; a different tool.

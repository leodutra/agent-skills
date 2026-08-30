# Changelog — Claude Code Context Stack

One line per change. The "why" lives in [`DECISIONS.md`](DECISIONS.md); entries
cite the decision they implement rather than restating it. Behavior is defined by
`stack-init.sh` / `stack-init.ps1` (D2) — this file records what moved and when.

Fix entries with no `D<n>` are defect repairs that changed no decision.

## 3.0

The stack stops intercepting and starts instructing. Three of the four tools are
removed; what remains is one opt-in tool and one instruction-injecting plugin.

- **Remove** Headroom and RTK. Headroom went on measurement: of 448,564 tokens it
  reported saving, 113,267 (25.3%) reached the wire, and four prefix-cache busts
  destroyed 155,045 cached tokens against 5,538 saved (≈$0.98 vs $0.069). RTK went
  on absence of evidence: its 60–90% claims carried no citation, and on the
  reference machine it was installed but inert (binary on PATH, no hook
  registered, no snapshot ever taken). [D51](DECISIONS.md#d51)
- **Remove** graphify, and with it every piece of per-repo state the stack had:
  `graphify-out/`, the graph-autobuild SessionStart hook, the four git refresh
  hooks, the worktrunk `post-start` hook, `.graphify-skip`,
  `CLAUDE_STACK_NO_AUTOBUILD`, and the graph-vs-LSP precedence spec. Orientation
  has no successor and none is planned. [D52](DECISIONS.md#d52)
- **Change** Serena is registered but no longer enabled by default. Turn it on
  with `/mcp` for refactor, test-writing, and architecture work on larger
  projects; leave it off for quick queries, small repos, and greenfield. The
  ~4×-on-cheap-lookups and ~24K-manifest figures behind this are external and
  flagged unverified. [D53](DECISIONS.md#d53)
- **Fix** Serena's manifest measured at **5,791 tokens** (24 tools, `claude-code`
  context), not the ~24K D53 cited from an external source — a ~4× overstatement,
  most likely a character count read as tokens. D53's decision stands but on
  different grounds: the tax is small and mostly cached, so what actually argues
  for opt-in is inert cost when Serena is never activated, plus the full
  prefix-cache bust that toggling it mid-session causes (D50's mechanism).
  [D55](DECISIONS.md#d55) (corrects [D53](DECISIONS.md#d53))
- **Add** good-readme to the global skill set, making it four: it is project-agnostic
  (every repo has a README) and the first global skill fronting no installed tool.
  D48's per-repo rule for domain skills is unchanged; only its "exactly three"
  bound moved. ~85 tokens per session. [D58](DECISIONS.md#d58) (amends
  [D48](DECISIONS.md#d48))
- **Add** ponytail as a default-on Claude Code plugin (marketplace
  `DietrichGebert/ponytail`, plugin `ponytail@ponytail`), installed by
  `stack-init` via the `claude plugin` CLI. Injects a minimal-code-discipline
  ruleset at session start. Requires `node` on the non-interactive PATH; without
  it the activation stays quiet rather than erroring. [D54](DECISIONS.md#d54)
- **Add** Serena is retained behind a mechanical kill criterion: `verify` now
  reports how many sessions ever actually called a Serena tool, read from
  Serena's own logs. Zero after ~10 real sessions means remove Serena *and*
  `stack-init`. Unlike D20's never-run benchmark, the gate collects itself.
  [D57](DECISIONS.md#d57), backlog B7
- **Remove** the anti-bypass rules that survived RTK. The contract had been
  spending tokens every session forbidding an MCP shell tool that
  `--context claude-code` already removes from Serena's surface. The exclusion
  itself stays, re-grounded on permission granularity: Claude Code gates Bash
  per command and MCP tools per tool, so enabling `execute_shell_command` would
  collapse per-command approval into one blanket grant.
  [D56](DECISIONS.md#d56) (re-grounds [D3](DECISIONS.md#d3))
- **Remove** `stack-init init` (built a graph that no longer exists) and
  `stack-init stats` (reported `rtk gain` and `headroom savings`), retiring
  [D29](DECISIONS.md#d29).
- **Change** contract rule 1 is now the guard that Serena may not be loaded,
  replacing the conditional that guarded against a missing graph. Rules 2–4 are
  scoped to enabled sessions; rule 6 records that orientation has no owner.
- **Fix** D3's stated reason is corrected: it justified disabling Serena's shell
  tool partly because MCP calls bypassed RTK's hook. With RTK gone that half is
  dead; the decision stands on duplicate-tool routing alone.
  [D53](DECISIONS.md#d53)

## 2.5

- **Add** the claude shim exports `HEADROOM_LOSSLESS=1`, which sets
  `ccr_inject_tool=False` in the proxy — dropping the injected `headroom_retrieve`
  tool, its retrieval markers, and the buffered-stream conversion that was
  turning streaming turns into `API returned an empty or malformed response
  (HTTP 200)`. Compression is kept (lossless compaction + marker-free
  SmartCrusher); `--no-ccr` was rejected because it compresses lossily with no
  recovery path. An explicit `HEADROOM_LOSSLESS` still wins.
  [D49](DECISIONS.md#d49) (narrows [D47](DECISIONS.md#d47))
- **Fix** the Headroom section gains boundary 6, recording *both* shim-pinned proxy knobs and the
  fact that neither binds a reused proxy. The `HEADROOM_MODE` pin shipped in
  2.4.1 had reached `DECISIONS.md` and this file but never the spec.
- **Fix** the bust attribution in D49 was under-determined. Headroom's
  tool-search deferral is recomputed every turn but delivered only on canonical
  turns, so the tools array — first in Anthropic's cache prefix — flips with the
  latch; deferral and latching are perfectly collinear across all seven
  multi-request sessions, and the "natural control" D49 cited had deferral off
  entirely. `HEADROOM_TOOL_SEARCH` stays on (no symptom, 13,647 measured
  tokens/request at stake); switching it off is recorded as the isolating
  experiment. [D50](DECISIONS.md#d50) (corrects [D49](DECISIONS.md#d49))
- **Fix** §7's cache-bust entry is no longer "unmeasured": it now carries the
  measured mechanism (a one-way `canonical`→`passthrough` latch once a signed
  thinking block enters history), its price, the proxy-log commands that detect
  it, and a warning that D41's ratio read 0.791 — healthy — through the very
  window in which four busts destroyed 155,045 cached tokens.
- **Add** `skills` subcommand on both installers: lists the repo's deployable
  skills, or deploys named ones into the CURRENT repo's `.claude/skills/` —
  symlink on Unix / junction on Windows by default (stays current with the
  checkout, machine-local, excluded via `.git/info/exclude`), `--copy` for a
  committable copy (marker-guarded so a refresh never clobbers a user's own
  same-named skill). Domain skills (architecture-blueprint,
  rust-bevy-architecture, rust-wgpu-functional, macro-analyst) stay out of the
  global install on purpose: every global skill's description is loaded into
  every session in every project. [D48](DECISIONS.md#d48)
- **Add** `verify` reports the current repo's `.claude/skills/` deployments
  (annotated link/copy) alongside the global skill rows.

## 2.4.1

Two inherited defaults become pinned decisions. Both were already correct today;
neither was held by anything.

- **Fix** Serena's dashboard no longer depends on a platform default. `web_dashboard_interface`
  is pinned on both installers — `tray_manager` on Windows, and on Unix only after
  probing the session bus for a StatusNotifier host *and* asking pystray which
  backend it bound, with `pygobject` injected into Serena's isolated `uv` venv
  first (without it pystray binds XEmbed and the icon is never drawn). Either
  probe failing pins `browser`. [D46](DECISIONS.md#d46) (narrows [D33](DECISIONS.md#d33))
- **Add** the claude shim exports `HEADROOM_MODE=cache`, which `headroom wrap`
  forwards to the proxy. A pin, not a change — it matches today's default and
  survives a flip of it. An explicit `HEADROOM_MODE` still wins. [D47](DECISIONS.md#d47) (narrows [D25](DECISIONS.md#d25))

## 2.4

- **Add** `gauntlet-loop` as a globally deployed standalone skill; it is
  catalogued in the root README and reported by both installers' `verify`.

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
- **Change** the Headroom section's boundary 5 no longer conditions Headroom on a benchmark nobody
  runs: retained on wire-token evidence, cache economics recorded as unverified,
  status provisional and monitored. [D37](DECISIONS.md#d37) (narrows [D20](DECISIONS.md#d20))
- **Change** spec split into spec / `DECISIONS.md` / `CHANGELOG.md`; enforced by
  review, not tooling. [D36](DECISIONS.md#d36), [D38](DECISIONS.md#d38)
- **Change** spec sections renumbered: Serena autoinit is §6.3; Windows §6.5;
  optional graphify MCP server; verification §8.
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

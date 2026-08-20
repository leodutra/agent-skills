# Decisions — Claude Code Context Stack

**Append-only.** A decision's body is never rewritten. When one is reversed,
narrowed, or its stated reason turns out to be wrong, append a *new* entry and
add a status line to the old one pointing at it. IDs are permanent and are what
[`CHANGELOG.md`](CHANGELOG.md) and [the spec](claude-code-context-stack.md) cite;
the spec carries no rationale of its own beyond a `D<n>` reference.

Why append-only: this file exists because a rationale that gets edited in place
loses the record that it was ever wrong — and the two most expensive defects
found so far (D33, D35) were both cases of a *stated reason* that had gone stale
while the decision it justified stayed correct. Keeping the wrong reason visible,
with its correction next to it, is the point.

| ID | Decision | Version | Status |
| --- | --- | --- | --- |
| [D1](#d1) | Docs/intent layer removed | 2.0 | Active |
| [D2](#d2) | One self-documenting installer per OS | 2.0 | Active |
| [D3](#d3) | Serena in `claude-code` context, shell disabled | 2.0 | Active |
| [D4](#d4) | Serena at user scope, no `--project` | 2.0 | Active — reason corrected by D33 |
| [D5](#d5) | `graphify claude install` dropped | 2.0 | Active — reason corrected by D35 |
| [D6](#d6) | graphify rebuild on git hooks, not agent hooks | 2.0 | Active |
| [D7](#d7) | graphify via CLI through Bash; MCP optional | 2.0 | Active |
| [D8](#d8) | Diagnostics from Serena, not compressed `cargo check` | 2.0 | Active |
| [D9](#d9) | `uv tool install` over plain `pip` | 2.0 | Active |
| [D10](#d10) | RTK input mode = manual capture | 2.0 | Active |
| [D11](#d11) | Serena launched from a pinned binary, not `uvx --from git+…` | 2.1 | Active |
| [D12](#d12) | Headroom added as a fourth, proxy-layer tool | 2.1 | Active |
| [D13](#d13) | Headroom's `--code-graph` / `--memory` never passed | 2.1 | Active — extended by D26 |
| [D14](#d14) | No automatic shell alias for `claude` | 2.1 | Superseded by D17 |
| [D15](#d15) | Uncommitted architectural questions get a refresh, not a ban | 2.2 | Active |
| [D16](#d16) | Four refresh hooks; staleness bounded to one git operation | 2.2 | Active |
| [D17](#d17) | Standalone `clw` wrapper instead of a shell alias | 2.2 | Superseded by D25 |
| [D18](#d18) | Rejected: a wrapper named `cc` | 2.2 | Active (constraint) |
| [D19](#d19) | Condensed contract injected into agent files | 2.2 | Active — user-global half moved to a hook by D43 |
| [D20](#d20) | Headroom's place is gated on a cache-economics benchmark | 2.2 | Narrowed by D37 — gate never ran |
| [D21](#d21) | Rejected: per-prompt structural-diff injection | 2.2 | Active (rejection) |
| [D22](#d22) | Rejected: folding graphify into Serena's MCP server | 2.2 | Active (rejection) |
| [D23](#d23) | Serena tool-surface audit deferred | 2.2 | Declined by D39 — the gate was uncollectable |
| [D24](#d24) | Per-repo init automated via SessionStart autobuild | 2.3 | Active |
| [D25](#d25) | `claude` shadowed by a recursion-safe shim | 2.3 | Active — default-on affirmed by D40 |
| [D26](#d26) | `--no-tokensave` probed and passed | 2.3 | Active — probe moved to launch by D44 |
| [D27](#d27) | `settings.json` is never clobbered on a parse failure | 2.3.1 | Active |
| [D28](#d28) | Repo state anchored on the repo root, not cwd | 2.3.1 | Active |
| [D29](#d29) | `stats` calls `headroom savings` | 2.3.1 | Active |
| [D30](#d30) | The contract text has exactly one copy | 2.3.2 | Active |
| [D31](#d31) | This repo's git hooks have one implementation | 2.3.2 | Active |
| [D32](#d32) | An optional install never aborts the run | 2.3.2 | Active |
| [D33](#d33) | Serena does not self-activate; serena-autoinit hook added | 2.3.3 | Active — corrects D4 |
| [D34](#d34) | Serena's language set derived from tracked files | 2.3.3 | Active |
| [D35](#d35) | `graphify claude install`'s hook is active, not a no-op | 2.3.3 | Active — corrects D5 |
| [D36](#d36) | Spec split into spec / decisions / changelog | 2.3.3 | Active — enforcement narrowed by D38 |
| [D37](#d37) | Cache-economics benchmark declined; Headroom provisional | 2.3.3 | Active — narrows D20; standing check made executable by D41 |
| [D38](#d38) | Mechanical doc-drift checking declined | 2.3.3 | Premise corrected, partly reversed by D42 — narrows D36 |
| [D39](#d39) | Serena tool-surface audit declined | 2.4 | Active — declines D23 |
| [D40](#d40) | Headroom stays default-on despite being the unverified layer | 2.4 | Active — affirms D25 |
| [D41](#d41) | The cache-bust symptom restated as a single-session ratio | 2.4 | Active — repairs the standing check in D37 |
| [D42](#d42) | Doc reference checking reinstated, Unix-scoped | 2.4 | Active — corrects the premise of D38 |
| [D43](#d43) | Condensed contract refreshed by hook, user-global scope only | 2.4 | Active — narrows D19 |
| [D44](#d44) | `--no-tokensave` probed at launch, cached on headroom's version | 2.4 | Active — narrows D26 |
| [D45](#d45) | `BACKLOG.md` as the fourth document | 2.4 | Active — extends D36 |
| [D46](#d46) | Serena's dashboard interface is pinned, and a tray is earned not assumed | 2.4.1 | Active — narrows D33 |
| [D47](#d47) | The shim pins Headroom to cache mode | 2.4.1 | Active — narrows D25 |
| [D48](#d48) | Domain skills deploy per-repo, never globally | 2.5 | Active |

---

<a id="d1"></a>

## D1 — Docs/intent layer removed

**Version:** 2.0 · **Status:** Active

The stack is only the token-reducing tools. Specs, ADRs, and worklogs are
*content*, not compression; scaffolding them (as 1.x did) added a maintenance
surface that drifted and a precedence tangle with no owner. Out of scope here.

<a id="d2"></a>

## D2 — One self-documenting installer per OS

**Version:** 2.0 · **Status:** Active

`stack-init.sh` / `stack-init.ps1` are the canonical executables and the source
of truth for *behavior*; the spec is the source of truth for *why*. One fact,
one home: change behavior in the script, record reasoning here.

<a id="d3"></a>

## D3 — Serena in `claude-code` context, shell disabled

**Version:** 2.0 · **Status:** Active

Running Serena under the `claude-code` context (formerly `ide-assistant`) makes
the RTK bypass impossible *structurally* rather than by instruction:
`execute_shell_command` is simply not in the tool surface, so the agent cannot
route tests around RTK's Bash hook even if it wants to. It also removes
duplicate `read_file` / `search_for_pattern` tools that confuse routing against
Claude Code's own.

<a id="d4"></a>

## D4 — Serena at user scope, no `--project`

**Version:** 2.0 · **Status:** Active — **reason corrected by [D33](#d33)**

> One registration serves every repo, activating from the session's cwd.
> Per-repo memories stay in each repo's `.serena/`, so there's no cross-project
> contamination; the only cost is first-session onboarding per repo.

The decision (register once at user scope, without `--project`) is correct and
still in force. The justification quoted above is **wrong**: Serena does not
activate from the session's cwd. See D33 for what actually happens and what was
added to close the gap.

<a id="d5"></a>

## D5 — `graphify claude install` dropped

**Version:** 2.0 · **Status:** Active — **reason corrected by [D35](#d35)**

> It would write a second, near-duplicate "read GRAPH_REPORT.md" directive into
> the same global `CLAUDE.md` as the routing contract, and its Glob/Grep
> PreToolUse hook is a no-op on Claude Code builds after the late-May-2026
> tool-architecture change.

Dropping it is correct and still in force. The second half of the justification
is **wrong** — the hook is active. See D35.

<a id="d6"></a>

## D6 — graphify rebuild on git hooks, not agent hooks

**Version:** 2.0 · **Status:** Active

Rebuilding on git events matches the graph's epistemic status (true as of the
last rebuild), avoids rebuild thrash, and keeps staleness bounded and *known*
rather than variable. Extended by D16 from post-commit alone to four hooks.

<a id="d7"></a>

## D7 — graphify via CLI through Bash; MCP optional

**Version:** 2.0 · **Status:** Active

CLI output flows through RTK's compression and costs zero standing tool
definitions. An MCP query server adds value only if the agent measurably
under-uses the graph, so it stays an opt-in escape hatch.

<a id="d8"></a>

## D8 — Diagnostics from Serena, not compressed `cargo check`

**Version:** 2.0 · **Status:** Active

Structured LSP data is already minimal and involves no lossy heuristic.
Compression belongs where output is noisy, not where it is already signal.

<a id="d9"></a>

## D9 — `uv tool install` over plain `pip`

**Version:** 2.0 · **Status:** Active

`uv` is already required for Serena, and plain `pip` is the most common cause of
`graphify: command not found` (PATH placement).

<a id="d10"></a>

## D10 — RTK input mode = manual capture

**Version:** 2.0 · **Status:** Active

A first-class "inject into the prompt at position X" mode is an unshipped
upstream proposal. Manual `$(rtk ...)` capture is the supported equivalent and
keeps placement under the caller's control.

<a id="d11"></a>

## D11 — Serena launched from a pinned binary, not `uvx --from git+…`

**Version:** 2.1 · **Status:** Active

`uvx` re-resolves the git ref and rebuilds the package whenever uv's cache is
cold, which overruns Claude Code's 30 s MCP startup limit and leaves the session
with **no Serena at all**. That failure is silent — the model falls back to grep
and nothing in the UI says contract rule 2 has become unenforceable. The
installer therefore also *migrates* an existing uvx-based registration (a bare
"already registered" check would preserve the bug forever) and sets
`env.MCP_TIMEOUT = 120000` as a safety net for a genuinely cold first launch.

<a id="d12"></a>

## D12 — Headroom added as a fourth, proxy-layer tool

**Version:** 2.1 · **Status:** Active

graphify, Serena, and RTK each eliminate a waste source *at its origin*, but
nothing among them was positioned to catch `Read`-tool file dumps or the
conversation history's own growth, both of which still reach the API
uncompressed. Headroom's proxy sits exactly there. It is additive on RTK's
output, never a substitute for it.

<a id="d13"></a>

## D13 — Headroom's `--code-graph` / `--memory` never passed

**Version:** 2.1 · **Status:** Active — extended by [D26](#d26)

`--code-graph` would have Headroom build a second structure graph, directly
duplicating graphify and reopening the layer-bleed problem the stack exists to
close: two derivations of the same question that can disagree. `--memory` is an
intent/memory feature, and this stack manages no intent layer by design (D1) —
adding one back through a flag would undo that decision by a side door.

<a id="d14"></a>

## D14 — No automatic shell alias for `claude`

**Version:** 2.1 · **Status:** **Superseded by [D17](#d17)**, then [D25](#d25)

The installer printed a reminder rather than writing a shell function. Two
reasons: editing a user's shell profile is a persistent, easy-to-miss change to
their environment that this installer otherwise avoids (it only ever touched
`CLAUDE.md` and `settings.json`, both Claude-owned); and a function literally
named `claude` risks recursing into itself depending on how `headroom wrap`
resolves the real binary on a given shell.

<a id="d15"></a>

## D15 — Uncommitted architectural questions get a refresh, not a ban

**Version:** 2.2 · **Status:** Active

2.1.1's rule 6 forbade the graph outright for any uncommitted work, assuming the
graph is inherently commit-bound. It isn't: it is bound to the *last rebuild*,
and `graphify update .` is incremental and content-hash cached — cheap. So an
architectural question mid-refactor can legitimately trigger refresh-then-query
instead of falling back to file-reading. Symbol-level questions about
uncommitted work still route to Serena, never the graph.

<a id="d16"></a>

## D16 — Four refresh hooks; staleness bounded to one git operation

**Version:** 2.2 · **Status:** Active

`post-commit` alone left the graph stale with no bound after any other
working-tree-moving operation. Added `post-checkout` (branch switches only,
`$3 = 1`, backgrounded so switching isn't blocked), `post-merge`, and
`post-rewrite` (fires once at the end of a rebase). All are written
merge-not-clobber: an existing hook without the stack's marker gets the refresh
line appended rather than being overwritten.

Worktrees are deliberately supported rather than forbidden: git hooks execute
with cwd at the root of whichever worktree triggered them and no absolute paths
are baked into any hook body, so the triggering worktree self-refreshes. Sibling
worktrees catch up on their next branch switch or via D15's on-demand refresh.
Residual accepted risk: a long-lived sibling that never switches branches and is
never asked an architectural question can sit stale indefinitely — nothing is
querying it in that state.

<a id="d17"></a>

## D17 — Standalone `clw` wrapper instead of a shell alias

**Version:** 2.2 · **Status:** **Superseded by [D25](#d25)**

A distinctly-named executable (`clw`, falling back to `hclaude`/`claudew`) in
`~/.local/bin` that `exec`s the real binary defeats both of D14's objections:
no profile mutation, and no self-recursion because it doesn't shadow `claude`.

<a id="d18"></a>

## D18 — Rejected: a wrapper named `cc`

**Version:** 2.2 · **Status:** Active (constraint)

`cc` shadows the system C compiler and breaks `cargo`/`gcc` toolchains that
resolve it on PATH. The constraint outlives the wrapper (removed in D25) and
binds anything future that shadows a command name.

<a id="d19"></a>

## D19 — Condensed contract injected into agent files

**Version:** 2.2 · **Status:** Active — user-global half moved to a hook by [D43](#d43)

Task-tool subagents get a fresh context that does not load `~/.claude/CLAUDE.md`.
RTK's hook (settings-level) and Headroom's env (process-level) both propagate
automatically; the routing contract is prose in one specific file and does not.
Without a mitigation, spawned agents grep for symbols and orient by file-reading
exactly where token volume is highest. A condensed ~6-line form (rules 1, 2, 5, 6
plus the precedence line) is injected between sentinel markers into every `*.md`
under `~/.claude/agents/` and `.claude/agents/`.

<a id="d20"></a>

## D20 — Headroom's place is gated on a cache-economics benchmark

**Version:** 2.2 · **Status:** **Narrowed by [D37](#d37)** — the gate was never run

Wire-level compression can bust Anthropic's prompt cache even while shrinking
wire tokens: recompressing history changes the bytes the API sees turn to turn,
and fewer wire tokens can still mean *more* money once cache misses are priced
in. Headroom is therefore retained conditionally, not assumed — see the
benchmark in the spec's verification section. If it comes out net-negative for a
usage pattern, the finding is recorded here rather than silently ignored.

<a id="d21"></a>

## D21 — Rejected: per-prompt structural-diff injection

**Version:** 2.2 · **Status:** Active (rejection)

Keeping the graph "live" by patching it every turn would be a standing token
cost on *every* turn, and would duplicate graphify's own parser in a second, ad
hoc form. D15's on-demand refresh gets the same correctness for a cost paid only
when an uncommitted architectural question is actually asked.

<a id="d22"></a>

## D22 — Rejected: folding graphify into Serena's MCP server

**Version:** 2.2 · **Status:** Active (rejection)

It would optimize subprocess launch latency (hundreds of ms) inside a workflow
dominated by inference latency (seconds); move graph output out from under RTK's
compression; enlarge and destabilize Serena's tool list (cache-bust risk, the
same mechanism as D20); and require forking upstream Serena — a maintenance
surface D2 explicitly eliminated. The optional standalone graphify MCP server
remains the sanctioned escape hatch if the agent under-uses the CLI graph.

<a id="d23"></a>

## D23 — Serena tool-surface audit deferred

**Version:** 2.2 · **Status:** **Declined by [D39](#d39)** — the gate was uncollectable

If, after enough `stack-init stats` snapshots, some Serena tools turn out never
to be invoked, they could be excluded via Serena's tool include/exclude config:
fewer standing tool-definition tokens and a more stable tool list (the same
prefix-cache-stability argument as D20). Not implemented speculatively — it is
gated on real usage data that does not exist yet.

<a id="d24"></a>

## D24 — Per-repo init automated via SessionStart autobuild

**Version:** 2.3 · **Status:** Active

The graph is irreducibly per-repo *state*, but the per-repo *step* was not
irreducible: a global SessionStart hook can detect "git repo, no graph" and build
it in the background. Two costs were weighed. First-session surprise (minutes of
background build on a big monorepo, plus a directory appearing unasked) is
mitigated by backgrounding, a one-line session note so the agent knows the graph
isn't ready, and two opt-outs. Tracked-file safety is handled *structurally*
rather than by care: the autobuild writes only under `.git/` — refresh hooks,
`info/exclude` instead of `.gitignore`, a mkdir-atomic build lock stale after 60
minutes so a killed build can't wedge a repo forever — because a background job
mutating files the user would have to commit is never acceptable. The
tracked-file conveniences stay in `stack-init init`, where a human asked for them.

<a id="d25"></a>

## D25 — `claude` shadowed by a recursion-safe shim

**Version:** 2.3 · **Status:** Active — supersedes [D17](#d17), [D14](#d14); default-on
affirmed by [D40](#d40)

Shadowing `claude` itself is now done deliberately, with D14's recursion hazard
bounded by construction instead of avoided by naming. An absolute-path handoff
turned out to be impossible: `headroom wrap` only accepts tool names (click
subcommands) and re-resolves `claude` on PATH itself, so re-resolution back onto
the shim is unavoidable. The bound comes from a re-entry guard — the shim exports
`CLAUDE_STACK_SHIM` before delegating, and when headroom's PATH search lands back
on the shim, that second entry `exec`s the real binary directly (resolved by the
shim, skipping its own directory). Exactly one bounce, never a loop. An
already-wrapped session (localhost `ANTHROPIC_BASE_URL`) is never double-wrapped;
headroom-missing and `CLAUDE_NO_HEADROOM=1` fall through to the real binary, so
the shim can degrade but never block.

D14's profile-mutation objection is narrowed, not dismissed: one marker-guarded
PATH line per rc file on Unix, one registry user-PATH prepend on Windows — both
idempotent and trivially removable. Known remaining gap: launchers that spawn the
binary without a PATH search (some IDE integrations) bypass the shim; the
SessionStart headroom-check catches those at runtime.

<a id="d26"></a>

## D26 — `--no-tokensave` probed and passed

**Version:** 2.3 · **Status:** Active — extends [D13](#d13); probe moved to launch
by [D44](#d44)

Upstream renamed and promoted the code-graph feature: newer headroom builds its
own "tokensave" code graph *by default*. An upstream default change does not
invert a deliberate decision here. The shim passes `--no-tokensave` when the
installed headroom's help advertises it (probed at install time, so older
versions without the flag still launch cleanly). Re-run `stack-init global` after
upgrading headroom so the probe re-runs.

<a id="d27"></a>

## D27 — `settings.json` is never clobbered on a parse failure

**Version:** 2.3.1 · **Status:** Active

Both installers used to fall back to an empty object when the file failed to
parse, then write it back — silently destroying RTK's `PreToolUse` hook, every
permission and every env var over one malformed byte. Both now hard-stop and
refuse to overwrite. The POSIX side also reads it as `utf-8-sig`, because the
Windows side used to write a BOM into the same file (`Set-Content -Encoding utf8`
under Windows PowerShell 5.1) and a plain `utf-8` read rejects that;
`stack-init.ps1` now writes BOM-less UTF-8 everywhere, so both platforms emit
identical bytes.

<a id="d28"></a>

## D28 — Repo state anchored on the repo root, not cwd

**Version:** 2.3.1 · **Status:** Active

`verify` reported "graph: not built / serena project: none" for a fully wired
repo whenever it ran from a subdirectory — which is the documented Windows
invocation — and `init` would have built a graph of that subdirectory alongside
the real one. Both now resolve through `git rev-parse --show-toplevel`, matching
what the autobuild hook already did.

<a id="d29"></a>

## D29 — `stats` calls `headroom savings`

**Version:** 2.3.1 · **Status:** Active

`headroom stats` has never been a headroom subcommand, so every snapshot ever
taken recorded a usage error instead of the numbers. (`headroom memory stats`
exists and is a different thing: memory-store counts, not compression savings.)
The spec kept citing the nonexistent form in two more places, in §7 and §9,
until they were found by reading in 2.3.3.

<a id="d30"></a>

## D30 — The contract text has exactly one copy

**Version:** 2.3.2 · **Status:** Active

The contract lived verbatim in `stack-init.sh`, again in `stack-init.ps1`, and a
third time in the spec — and the two installers had already drifted (em dashes on
the POSIX side, hyphens on the Windows side) while claiming to write the same
managed block into the same `~/.claude/CLAUDE.md`. Both now read `contract.md` and
`contract-condensed.md`, and the spec points at them rather than quoting them.
Those files are ASCII-only because Windows PowerShell 5.1 decodes a BOM-less file
as ANSI. A normative text quoted in three places drifts; this one already had.

<a id="d31"></a>

## D31 — This repo's git hooks have one implementation

**Version:** 2.3.2 · **Status:** Active

`init` carried its own copy of the `post-checkout`/`post-merge`/`post-rewrite`
bodies and called `graphify hook install` directly, so it never gained the
dead-interpreter pin repair the SessionStart hook grew. The generated hook now
accepts `--hooks`/`-Hooks` and `init` delegates to it — which also means writing
the hook file is split from registering it.

<a id="d32"></a>

## D32 — An optional install never aborts the run

**Version:** 2.3.2 · **Status:** Active

`check_deps` only *warns* about a missing `cargo`/`pip`, but `set -e` then turned
the `cargo install` / `pip install` / `rtk init -g` that followed into an abort,
taking out every later step including the routing contract — the one thing the
script exists to write. Each optional install is now guarded and warns, matching
what the Windows side already did.

<a id="d33"></a>

## D33 — Serena does not self-activate; serena-autoinit hook added

**Version:** 2.3.3 · **Status:** Active — **corrects [D4](#d4)**

D4 justified the bare user-scope registration with "Serena activates the project
from the session's cwd, so one registration serves every repo." That is false.
Serena is not cwd-aware: registered bare it starts with **no active project**,
and until something calls `activate_project` every symbol tool answers "No active
project". The failure is silent in the worst way — the model falls back to grep
and nothing in the UI reports that contract rule 2 has stopped being enforceable,
the same shape as D11's timed-out MCP launch.

D4's *decision* survives; only its reason changes. A user-scope registration has
to be repo-agnostic because it is shared by every checkout, and `--project` would
pin it to one and be wrong in all the others. Activation is a separate problem
and gets a separate mechanism: a `SessionStart` hook
(`~/.claude/hooks/serena-autoinit.sh` / `.ps1`) that, inside a git repo, writes or
repairs `.serena/project.yml` for that checkout and **always** ends by emitting
the project's name and path plus the instruction to call `activate_project` —
on every path through the hook, because writing the config does not activate it.

Constraints that fell out of building it:

- Everything it writes stays untracked — `.serena/` goes into `.git/info/exclude`
  in the *common* git dir (one entry covers the main checkout and every worktree),
  never a tracked `.gitignore`. Same rule as D24.
- A linked worktree is a separate project, because
  `project_serena_folder_location` is `$projectDir/.serena`. `serena_config.yml`
  keys its registry by path, but *names* are what activation and the dashboard
  display, so linked worktrees are suffixed `repo@branch` to stay distinct.
- The main checkout gets `ignored_paths: [".claude/worktrees"]`, because worktrunk
  nests linked worktrees *inside* it and one symbol lookup would otherwise return
  a near-duplicate hit per branch. Emitted unconditionally — worktrees usually
  appear after the file is generated, and it is inert when the dir doesn't exist.
- Serena binds a project's language servers when it first activates it. Editing
  `project.yml`, or re-calling `activate_project` in the same session, does not
  reload them; a **new session** is required. A repair is therefore verified by
  reading the file, not by re-running a Serena tool in the same session.

Rejected alternative: pinning `--project` per repo, which reintroduces a per-repo
install step and multiplies user-scope registrations — the thing user scope
exists to avoid.

<a id="d34"></a>

## D34 — Serena's language set derived from tracked files

**Version:** 2.3.3 · **Status:** Active

Delegating language detection to Serena is not safe to build a contract on. On
this repo — 21 markdown files, one `.sh`, one `.ps1` — its auto-detection selected
`powershell` **alone**, after which every other file answered "path is ignored" /
`Cannot extract symbols … Active language servers: ['powershell']`. Because
contract rule 2 routes *all* symbol work to Serena, a detection miss doesn't
degrade one query: it disables the layer for most of the repo while continuing to
look like it works.

A `git ls-files` extension scan is deterministic and complete for the checkout.
Two implementation constraints:

- Compiled/checked languages are emitted **first**, because the first entry is
  Serena's default and fallback server — a real language must outrank
  `markdown`/`yaml`/`toml`.
- Repair of a foreign config is gated on a language-coverage **subset** check, not
  on the stack's marker header. Serena rewrites `project.yml` into its own
  commented template on activation and strips the header, so a marker test would
  re-repair forever. The subset check is idempotent: it fires only when a language
  actually present in the checkout is missing from the config.

Repair is never destructive: the original is kept at `project.yml.bak-<ts>` and
the `project_name` it was registered under is preserved, so an intentionally
renamed project does not silently change identity. A file that still carries the
stack's marker is left alone permanently, so hand edits survive every session.

<a id="d35"></a>

## D35 — `graphify claude install`'s hook is active, not a no-op

**Version:** 2.3.3 · **Status:** Active — **corrects [D5](#d5)**

D5 dropped `graphify claude install` partly on the claim that its Glob/Grep
PreToolUse hook "is a no-op on Claude Code builds after the late-May-2026
tool-architecture change." It is not: the hook is confirmed active and fires
unconditionally on every matching Bash/Read/Glob call.

D5's *decision* survives on two reasons that were always true and are now the
whole justification. First, `graphify claude install` targets the `CLAUDE.md` /
`.claude/settings.json` in the **current directory**, not the global `~/.claude`
this installer owns — the wrong layer for a global install step — and what it
writes there is a second, near-duplicate "read GRAPH_REPORT.md" directive
competing with the routing contract. Second, firing unconditionally is *noisier*
than contract rule 1, which scopes graphify to architecture questions.

The correction matters beyond bookkeeping: the spec's layer-bleed mitigation was
resting on "the hook does nothing anyway" rather than on either real reason. If
per-repo defense-in-depth is ever wanted, the place to wire the hook is
`stack-init init`, not the global step.

<a id="d36"></a>

## D36 — Spec split into spec / decisions / changelog

**Version:** 2.3.3 · **Status:** Active — enforcement narrowed by [D38](#d38)

The single document had become its own drift source. Its changelog had grown into
the largest section and narrated the same rationale as the decisions log, so a
correction had to be written twice and could — and did — land in only one place.
Three defects found in 2.3.3 (D33, D35, D29) were all *stale prose describing
shipped behavior correctly recorded elsewhere*.

The split: the spec keeps only what an operator or agent needs in the moment
(layer model, boundaries, routing matrix, precedence, install surface, failure
modes, verification) and carries no rationale beyond a `D<n>` citation;
`DECISIONS.md` is append-only and owns every "why"; `CHANGELOG.md` is one terse
line per change pointing at a decision. Rationale then has exactly one home, the
same rule D30 applied to the contract text and D2 applied to behavior.

Enforcement of the split is by review, not by tooling. A mechanical checker
was written and then removed the same day — see D38 for why, and for what the
split therefore relies on instead.

<a id="d37"></a>
## D37 — Cache-economics benchmark declined; Headroom retained provisionally

**Version:** 2.3.3 · **Status:** Active — narrows [D20](#d20); its standing check
made executable by [D41](#d41)

D20 said Headroom is "retained only as long as the cache-economics benchmark
shows it's net-positive on effective cost." That benchmark has never been run,
and there is no plan to run it. A conditional that is never evaluated does not
gate anything — so as written, D20 made the spec assert a control that did not
exist, the same defect class as D4's and D5's stale reasons and D29's phantom
subcommand. This entry records the decision rather than letting the claim drift.

**Decision:** the benchmark is **declined**, not pending. Headroom stays in the
stack on **wire-token evidence alone**, and its cache economics are recorded as
**unverified**. Its status is provisional and monitored, not established.

**Why declined.** The benchmark requires two full matched sessions per
Headroom-affecting change, hand-compared across four token counters, with the
confound it is meant to isolate (prompt-cache behavior) partly controlled by
upstream code — CCR's tool injection — that can change between runs. The cost is
real and recurring; the result would be valid only until the next upstream
release. Against that, the mitigation it would inform is already available and
free: Headroom is the only per-launch-optional layer, so if the §7 symptom
appears, the response is to launch bare, and nothing else in the stack is
affected. Measuring is not the cheapest path to the action the measurement would
recommend.

**What replaces it.** The §7 symptom — `headroom savings` reporting savings while
`cache_read_input_tokens` collapses — is the standing check, watched in ordinary
use rather than in a controlled run. The procedure stays documented in the spec's
verification section so the question remains answerable on demand: run it if the
symptom appears, or before anyone proposes making Headroom non-optional.

**What this costs.** "Headroom saves money" is unproven and must not be stated as
fact anywhere in the docs; only "Headroom reduces wire tokens" is supported. If
the cache-bust effect is real and large, the stack is currently paying for it and
would not know — accepted, bounded by Headroom being the one layer that can be
dropped per launch with no other consequence.

<a id="d38"></a>
## D38 — Mechanical doc-drift checking declined

**Version:** 2.3.3 · **Status:** **Premise corrected, partly reversed by
[D42](#d42)** — narrows [D36](#d36)

A checker was written for the drift class D36 describes: extract every
`tool subcommand` named in the docs, assert each appears in that tool's help;
likewise every `§` reference and every `D<n>` citation. It worked — on its first
run it caught a stale `§9` in the README and a `wt` that resolved to Windows
Terminal rather than worktrunk. It is still removed.

**Why.** It was a third implementation language sitting beside `stack-init.sh`
and `stack-init.ps1` in a repo whose direction is *fewer* implementations — the
same pressure behind D2, D30 and D31, and behind the pending consolidation into
one binary. A doc checker is not the thing worth spending that budget on, and
keeping it would have meant maintaining Python tooling through the .ps1 retirement
for a benefit review already provides.

**What the split relies on instead.** Review. Section renumbering and `D<n>`
citations are checked by reading, as the prose claims always were — and the three
defects that motivated this whole version (D33, D35, D29) were *all* found that
way, not by tooling. The checker would have caught D29's phantom subcommand and
neither of the other two, which is a fair statement of its actual ceiling.

**What this costs.** Renumbering a spec section can silently break a reference in
three other files, and nothing will say so. Accepted: the blast radius is a wrong
pointer in a doc, not wrong behavior, and the doc set is small enough to re-read.
If it stops being small enough, the place for these checks is the invariant-test
layer, not a standalone script.

<a id="d39"></a>
## D39 — Serena tool-surface audit declined

**Version:** 2.4 · **Status:** Active — declines [D23](#d23)

D23 deferred the audit "gated on real usage data" from `stack-init stats`
snapshots. `stats` records exactly two fields, `rtk gain` and `headroom savings`,
and nothing anywhere in the stack counts Serena tool invocations. The gate could
never fire — the defect class D37 named, left standing one entry away from where
it was found.

**Decision:** the audit is **declined**, not deferred. Serena's tool set stays as
`--context claude-code` leaves it.

**Why declined.** The win is a one-time reduction in standing tool-definition
tokens, and the surface is already narrowed structurally: D3's context flag
removes the shell, read and search tools, which were the bulk of it. Collecting
the evidence to trim further means building a telemetry subsystem — an OTEL
reader for `claude_code.tool.decision`, or a transcript scanner for
`mcp__serena__*` — and mirroring it in `stack-init.ps1`, in a repo whose stated
direction is fewer implementations (D2, D38). Against that cost, the failure mode
of getting it wrong is the worst shape in the stack: an excluded tool that turns
out to be needed produces "No active project"-style silence, the model falls back
to grep, and contract rule 2 is unenforceable with nothing in the UI to say so
(§7). This is D37's calculation applied to a smaller prize — measuring is not the
cheapest path to the action the measurement would recommend.

**What this costs.** The stack carries some number of Serena tool definitions it
may never invoke, and will not learn which. Accepted: the cost is a fixed,
cached prefix, not a per-turn one.

<a id="d40"></a>
## D40 — Headroom stays default-on despite being the unverified layer

**Version:** 2.4 · **Status:** Active — affirms [D25](#d25)

Raised as a defect: D25 leaves the stack's largest machine footprint — rc-file
PATH lines, a registry PATH prepend and three shim files on Windows, a re-entry
guard, a bypass variable, a runtime detection hook, a `verify` PATH check —
serving Headroom, the one layer D37 records as unverified, provisional and
monitored. RTK and Serena, both established, mutate no PATH. The apparent
conclusion is that invasiveness should track evidence.

**Decision:** the shim stays default-on, unchanged. Recorded deliberately rather
than left implicit.

**Why.** The premise conflates two independent axes. The shim's size is set by a
*technical* constraint D25 already documents: `headroom wrap` accepts only tool
names and re-resolves `claude` on PATH itself, so an absolute-path handoff is
impossible and the guard machinery is what bounds the resulting re-entry. RTK and
Serena need no PATH mutation because they wire into the *session* — a settings
hook and an MCP registration — not into the launch command. That is an
architectural difference, not a statement about evidence.

The two alternatives are both dominated. Making the shim pass through unless
`CLAUDE_HEADROOM=1` keeps the entire footprint while delivering nothing by
default. Restoring D17's `clw` reverts to the arrangement D25 superseded because
nobody types it. Either way Headroom goes inert for the launches people actually
perform, discarding the one thing D37 says *is* established — that it reduces
wire tokens — in order to hedge the part that is unproven.

And D37's mitigation is not foreclosed. "Launch bare" is one variable away:
`CLAUDE_NO_HEADROOM=1` is implemented in the shim, documented in the README's
escape hatches, and falls through to the real binary. The unverified half is
cache economics; the per-launch escape hatch is exactly the control for it. The
established half is what default-on delivers.

**What this costs.** A user who never reads the escape hatches runs an unproven
layer by default. Bounded by the footprint being marker-guarded and idempotent on
both platforms, so removal is one edit per rc file plus a directory.

<a id="d41"></a>
## D41 — The cache-bust symptom restated as a single-session ratio

**Version:** 2.4 · **Status:** Active — repairs the standing check in [D37](#d37)

D37 declined the cache-economics benchmark and substituted "watch the §7 symptom
in ordinary use." §7 defined that symptom as `cache_read_input_tokens` collapsing
**relative to a bare session** — which requires the matched bare run that step 1
of the declined benchmark specifies. The replacement check silently depended on
the thing it replaced, so nothing was being watched. The decision to decline was
sound; only its substitute was broken.

**Decision:** the standing check is restated in terms observable inside one
wrapped session, with no baseline.

**The signal.** A prefix-cache bust has a distinct single-session signature.
When the cache works, conversation history is stable, so as a session grows each
turn reads a large cached prefix and creates only the new turn's delta:
`cache_read_input_tokens` dominates and `cache_creation_input_tokens` stays
small. When Headroom recompresses history turn to turn, the prefix bytes change
every turn, so the cache never hits: `cache_creation_input_tokens` re-pays
approximately the whole conversation each turn while `cache_read_input_tokens`
stays flat near zero.

**The threshold.** After roughly ten turns, read
`cache_read / (cache_read + cache_creation)` off `/cost`. Healthy sessions sit
well above 0.5 and climb as history grows. Near zero, with `cache_creation`
tracking total conversation size, means the prefix is being invalidated every
turn — the failure D37 accepted the risk of. Response is unchanged: launch bare.

**Why this and not "unmonitored".** The alternative was to admit Headroom's cache
economics are unwatched and strip the claim from §2.4 boundary 5. That was not
necessary: the signal exists, costs nothing, and needs no second session. The
full benchmark stays declined and stays documented in §8 for the case where the
ratio does look wrong and someone wants the effective-cost number.

<a id="d42"></a>
## D42 — Doc reference checking reinstated, Unix-scoped

**Version:** 2.4 · **Status:** Active — corrects the premise of [D38](#d38)

D38 removed a working doc checker because it "was a third implementation language
sitting beside `stack-init.sh` and `stack-init.ps1`." That is wrong for the Unix
half: `stack-init.sh` already embeds Python heredocs for every `settings.json`
merge and for `stats`, and `check_deps` makes `python3` a hard prerequisite that
aborts the install when missing. On that platform the checker added no language
and no dependency. It is right for the Windows half, where `stack-init.ps1` does
the same merges in PowerShell.

D38's remaining reasons survive: maintaining tooling through the `.ps1`
retirement is real cost, and the checker's own ceiling was fairly stated — of the
three defects that motivated 2.3.3 it would have caught one.

**Decision:** the two purely textual checks come back as `stack-init verify
--docs`, on Unix only. Every `§` reference resolves to a real heading in the
spec; every `D<n>` citation resolves to an entry in `DECISIONS.md`. The third
check — tool subcommands named in the docs against that tool's `--help` — stays
dropped: it needs the tools installed, it is slow, and it has one hit in the
project's entire history (D29).

**Why the gap won.** The drift is not hypothetical. It produced a second instance
while this backlog was being worked: `README.md`'s file table still read
"(D1–D37)" after D38 was appended, found by reading. What comes back is ~40 lines
inside the heredoc pattern already in the file, over six documents, reading text
and matching strings — no network, no tool invocation, no new dependency.

**Why Unix only.** `--docs` validates *this repo's own documentation*, not a
user's installation. It is a maintenance check for whoever edits the doc set; a
Windows user of the stack has no occasion to run it. Scoping it there is
deliberate and is the one sanctioned exception to D2's equivalence rule, which
otherwise still binds: every behavior that touches a user's machine is mirrored.

**What this costs.** One subcommand that exists on one platform. Accepted, and
declared, rather than mirrored into PowerShell for symmetry alone.

<a id="d43"></a>
## D43 — Condensed contract refreshed by hook, user-global scope only

**Version:** 2.4 · **Status:** Active — narrows [D19](#d19)

D19 writes the condensed contract into every `*.md` under `~/.claude/agents/` and
`.claude/agents/` when the installer runs. D30 exists because a normative text
kept in several places drifts, and had. D19 puts a derivative of that text into an
unbounded number of files across checkouts, re-synced only when someone re-runs
`stack-init`. Every comparable per-repo concern was converted from an install-time
write to a self-healing SessionStart hook — D24 for the graph, D33 for Serena.
This was the one that was not.

**Decision:** a `contract-refresh` SessionStart hook re-injects the condensed
contract into `~/.claude/agents/*.md` at every session start, marker-guarded and
sentinel-replaced, reusing the same injection routine the installer calls.
`.claude/agents/` is **not** touched by the hook and stays with `stack-init init`.

**Why the split is not a compromise.** D24 settled that a background job must
never mutate files the user would have to commit; that is why autobuild writes
only under `.git/`. `~/.claude/agents/` is untracked user configuration, so the
rule does not bind there — and it is the copy that spans every project and goes
stale invisibly. `.claude/agents/` is tracked, so the rule does bind. Staleness
there is also the benign case: it surfaces as a reviewable diff the next time
someone runs `init`, not as silent drift.

**What this costs.** A fourth SessionStart hook. Its body is a directory glob and
a marker comparison over user-global files, with no git or network work, so the
added session-start latency is negligible.

<a id="d44"></a>
## D44 — `--no-tokensave` probed at launch, cached on headroom's version

**Version:** 2.4 · **Status:** Active — narrows [D26](#d26)

D26 probes the flag once at install time and bakes the answer into the shim,
mitigated by the instruction "re-run `stack-init global` after upgrading
headroom." Nobody re-runs it. Upgrade headroom and the baked flag silently stops
matching the installed build — silently restoring the duplicate code graph D13
forbids. §1's stated principle is structural over instructional; this was the
instructional one, guarding a boundary the stack calls hard.

**Decision:** the shim probes at launch and caches the result keyed on `headroom
--version`. A cache miss runs the `--help` probe once and writes the answer; every
later launch on that version reads the file. An unreadable version or a failed
probe falls back to passing no flag, which is the behavior older headrooms need
anyway. The "re-run after upgrading" instruction is dropped from §6.1 step 4. It
stays in D26's body, which is never rewritten; that body gets a status line
pointing here, which is what marks the instruction dead.

**Why not the alternatives.** Probing `--help` on every launch costs a slow
subprocess per session for an answer that changes only on upgrade. Passing the
flag optimistically and retrying on a non-zero exit cannot distinguish an unknown
flag from a genuine failure, and the retry would mean re-launching an interactive
session.

**What this costs.** One `headroom --version` subprocess per `claude` launch.
Accepted: it runs once per session, and it converts an instruction nobody follows
into a mechanism that cannot be skipped.

<a id="d45"></a>
## D45 — `BACKLOG.md` as the fourth document

**Version:** 2.4 · **Status:** Active — extends [D36](#d36)

D36 split the spec three ways: spec, decisions, changelog. It has no slot for
work that is *known wrong and not yet fixed*. That state had been living in the
decisions log as deferrals — D20's unrun benchmark, D23's uncollectable gate —
where an entry that reads `Deferred` is indistinguishable from one that has
quietly become permanent, which is how both of those defects survived.

**Decision:** `BACKLOG.md` holds open defects in the decision set, one item each,
ordered by cost. It carries no rationale — D36's rule applies to it unchanged.
Closing an item means appending a decision, adding a changelog line, and deleting
the item, so the file trends empty rather than accumulating. An item left long
enough to feel permanent is itself a decision to decline the work, and is written
as one.

**Why it is not a fourth source of truth.** It states only what is wrong, the
evidence, and what "done" looks like. Every "why" it would otherwise carry is the
decision that closes it. The file is the queue; `DECISIONS.md` remains the record.

<a id="d46"></a>
## D46 — Serena's dashboard interface is pinned, and a tray is earned not assumed

**Version:** 2.4.1 · **Status:** Active — narrows [D33](#d33)

Serena starts one instance per Claude session, each on its own port, and ships
`web_dashboard_open_on_launch: true`. With D33's autoinit hook making Serena
useful in *every* repo, that default turned into a browser tab per session. Both
installers already set it to `false`. That half was right and is unchanged.

The other half was not. `web_dashboard_interface` was left empty on Unix, which
means "platform default" — a value Serena chooses and may change. The comment
justifying it said Linux tray support was "environment-dependent and untested",
which was true of the *guess* nobody had made, not of the question: on this
platform the answer is directly observable, and turned out to be yes.

**Decision:** pin the interface on both platforms. Windows pins `tray_manager`
unconditionally — Serena documents it as fully supported there. Unix pins it only
after confirming the two independent conditions a tray actually needs, because
neither implies the other:

1. a `org.kde.StatusNotifierWatcher` owner on the session bus (`busctl --user`), and
2. a pystray backend that can talk to one — `_appindicator`, `_gtk` or `_darwin`,
   asked of pystray directly rather than inferred.

Condition 2 also has to be *created*, not just measured: Serena runs from an
isolated `uv` tool venv that cannot see a system `python-gobject`, so pystray
falls back to `_xorg` (XEmbed), which no current bar hosts and which fails by
drawing nothing at all. The installer injects `pygobject` into that venv first,
best-effort, via `uv pip install --python <that venv>` rather than
`uv tool install --with` — the latter re-resolves Serena from git and would
silently upgrade it as a side effect of configuring a dashboard. When either
condition stays false, the pin is `browser`.

**Why pin `browser` rather than leave it empty.** Empty is not a neutral value,
it is a deferral to a default that can move — which is how the per-session tabs
appeared in the first place. A recorded `browser` fails visibly if Serena changes
its mind; an empty key fails by quietly reopening windows.

**Why not detect from `$XDG_CURRENT_DESKTOP`.** It answers neither question. A
bar can host an SNI tray while pystray still cannot reach it, and the desktop
name says nothing about what is inside Serena's venv. Both facts are cheap to
observe directly, so observing them is strictly better than a table of desktop
names that would need maintaining.

**What this costs.** A source build of `pygobject` (needs
`gobject-introspection` headers) at install time on Linux, and two subprocesses
in the dashboard step. Both are best-effort: every failure path lands on
`browser`, which is exactly the behaviour this decision replaces.

<a id="d47"></a>
## D47 — The shim pins Headroom to cache mode

**Version:** 2.4.1 · **Status:** Active — narrows [D25](#d25)

Headroom's proxy has two optimization modes. `token` rewrites prior turns for
maximum compression; `cache` freezes them so the provider's prefix cache keeps
hitting. They trade directly against each other, and the trade is lopsided in a
Claude Code session: a proxy log line from this repo shows one request saving
1,205 tokens of compression while busting a 44,900-token cache read.

That is D20's cache-economics question, which D37 declined to benchmark and D41
restated as a ratio you can read off a single session. What neither noticed is
that the *mode* was never pinned. It was inherited — currently `cache` by
default, but a default the stack neither states nor holds.

**Decision:** the shim exports `HEADROOM_MODE=cache` before delegating, which
`headroom wrap` forwards to the proxy it spawns. This is a pin, not a change: it
matches today's default and keeps matching if that default moves. Written with
`:-` (POSIX) / an emptiness test (PowerShell) so an explicit `HEADROOM_MODE` in
the environment still wins — a floor, not a policy, the same rule
`set_global_env_var` follows for `MCP_TIMEOUT`.

**Why the shim and not `settings.json`.** `env` in `settings.json` reaches
Claude Code, not the proxy process `headroom wrap` starts. The shim is the only
place that is in both processes' ancestry.

**Why not `--mode cache` on the command line.** `headroom wrap claude` forwards
every unrecognised flag to `claude`; `--mode` is a `headroom proxy` flag, so
passing it there hands it to the wrong program. The env var is the supported
route, and `wrap` forwards it deliberately.

**What this costs.** Nothing at present — it selects the mode already in effect.
Its value is entirely in the failure it forecloses: an upstream default flip
silently trading this stack's cache hits for a few hundred compressed tokens,
with D41's ratio as the only thing that would ever notice.


<a id="d48"></a>

## D48 — Domain skills deploy per-repo, never globally

**Version:** 2.5 · **Status:** Active

The global install deploys exactly three skills to `~/.claude/skills/`
(gauntlet-loop, opensrc, worktrunk) and that set does not grow. The repo's
remaining skills — architecture-blueprint, rust-bevy-architecture,
rust-wgpu-functional, macro-analyst — are DOMAIN skills, and they get a new
`skills` subcommand on both installers that deploys them into the current
repo's `.claude/skills/` instead.

**Why not global.** Every skill in `~/.claude/skills/` pays its description
frontmatter into every session's context, in every project, relevant or not.
Measured on the four domain skills as written, that is roughly a thousand
tokens of standing overhead per session — charged to markdown repos, shell
repos, and everything else that can never trigger them — plus the occasional
spurious trigger from a plausible-but-wrong description match. For a stack
whose entire premise is killing wasted context, a Bevy skill's description in
a non-Bevy session is the same waste one layer up. The three global skills
earn their seat by being project-agnostic: they surface globally installed
tools and apply to any repo.

**Why symlink-first.** `skills <name>` symlinks (Unix) or junctions (Windows —
needs no Developer Mode, unlike a true symlink) the repo's canonical skill
directory into the target repo, so edits to the canonical copy are live
everywhere at once. This is D43's lesson applied in advance: install-time
copies go stale, and the fix there was to stop copying. A link's target is an
absolute path on one machine, so the deployment is excluded via
`.git/info/exclude` (the machine-local channel every SessionStart hook already
uses; written slashless, because a slash-terminated gitignore pattern matches
only real directories and a symlink is not one to git). `--copy` inverts the
trade for repos shared with collaborators: committable and portable, refreshed
only by re-running, left out of the exclude so git can track it.

**The marker rule.** A copied deployment carries a `.claude-context-stack`
marker file, and the command refuses to touch any directory that is neither a
link nor marker-carrying — the same principle as the serena-autoinit header:
managed state is replaceable precisely because it is labeled, and a user's own
same-named skill is never clobbered.

**What this costs.** Per-repo deployment is a manual, per-checkout step —
there is no SessionStart hook auto-linking skills by project type, on purpose:
which domain method applies to a repo is a judgment call, not something
derivable from file extensions the way serena-autoinit's language list is.

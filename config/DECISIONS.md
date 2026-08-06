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
| [D19](#d19) | Condensed contract injected into agent files | 2.2 | Active |
| [D20](#d20) | Headroom's place is gated on a cache-economics benchmark | 2.2 | Narrowed by D37 — gate never ran |
| [D21](#d21) | Rejected: per-prompt structural-diff injection | 2.2 | Active (rejection) |
| [D22](#d22) | Rejected: folding graphify into Serena's MCP server | 2.2 | Active (rejection) |
| [D23](#d23) | Serena tool-surface audit deferred | 2.2 | Deferred |
| [D24](#d24) | Per-repo init automated via SessionStart autobuild | 2.3 | Active |
| [D25](#d25) | `claude` shadowed by a recursion-safe shim | 2.3 | Active |
| [D26](#d26) | `--no-tokensave` probed and passed | 2.3 | Active |
| [D27](#d27) | `settings.json` is never clobbered on a parse failure | 2.3.1 | Active |
| [D28](#d28) | Repo state anchored on the repo root, not cwd | 2.3.1 | Active |
| [D29](#d29) | `stats` calls `headroom savings` | 2.3.1 | Active |
| [D30](#d30) | The contract text has exactly one copy | 2.3.2 | Active |
| [D31](#d31) | This repo's git hooks have one implementation | 2.3.2 | Active |
| [D32](#d32) | An optional install never aborts the run | 2.3.2 | Active |
| [D33](#d33) | Serena does not self-activate; serena-autoinit hook added | 2.3.3 | Active — corrects D4 |
| [D34](#d34) | Serena's language set derived from tracked files | 2.3.3 | Active |
| [D35](#d35) | `graphify claude install`'s hook is active, not a no-op | 2.3.3 | Active — corrects D5 |
| [D36](#d36) | Spec split into spec / decisions / changelog + a fitness test | 2.3.3 | Active |
| [D37](#d37) | Cache-economics benchmark declined; Headroom provisional | 2.3.3 | Active — narrows D20 |

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

**Version:** 2.2 · **Status:** Active

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

**Version:** 2.2 · **Status:** Deferred — gated on usage data

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

**Version:** 2.3 · **Status:** Active — supersedes [D17](#d17), [D14](#d14)

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

**Version:** 2.3 · **Status:** Active — extends [D13](#d13)

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
The spec kept citing the nonexistent form in two more places until D36's fitness
test was added to catch exactly this.

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

## D36 — Spec split into spec / decisions / changelog, plus a fitness test

**Version:** 2.3.3 · **Status:** Active

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

The fitness test (`tests/check-doc-commands.py`) exists because this class of
drift is mechanically detectable and was not being detected. It extracts every
command and subcommand named in the docs and asserts each appears in the
corresponding tool's help output — `headroom stats` (D29), which does not exist,
would have failed it for two versions. It also checks that every `§` cross-reference resolves to a real
section and that every cited `D<n>` exists, since the split made both newly
breakable. It is a *fitness function*, not a unit test: it constrains the
documentation to stay true, and it can only ever catch drift that is checkable
against a machine-readable source. Prose claims about behavior — D4's and D5's
wrong reasons — remain outside its reach and are still caught only by reading.

<a id="d37"></a>
## D37 — Cache-economics benchmark declined; Headroom retained provisionally

**Version:** 2.3.3 · **Status:** Active — narrows [D20](#d20)

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

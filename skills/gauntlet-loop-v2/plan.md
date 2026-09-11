# Plan: gauntlet-loop

Status: draft for review. Inputs: `intent.md` (the contract) and `spec.md` (requirements `FR-*`, acceptance criteria `AC-*`, concerns `C*`) beside this file. Baseline: `skills/gauntlet-loop` at commit 076dad3. Toolchain observed on 2026-09-10: Python 3.14, Node 26, `gh` 2.100, Claude Code 2.1.267, git 2.55; the repository has no CI directory. The global installer (`config/stack-init.sh`) mirrors a whole skill folder with `rm -rf` then `cp -R`, so everything the skill ships must live inside its folder.

The plan follows the intent's delivery order: outcomes 1, 2, 3, 4, 5, 14, 15, 16 (the holes), then 17 (the controller), then 6 and 6b (cost), then 7 to 13. Each outcome is one phase, one commit, one README entry, and the skill is usable after every phase.

## 1. Strategy

### 1.1 Where the work happens

- The folder that holds this plan becomes the skill. Phase 0 copies the baseline files into it; the last phase moves it over `skills/gauntlet-loop`. `intent.md`, `spec.md` and this plan move to `design/` inside the folder in phase 0, so the ledger can link them and the mirror carries them (they are never loaded into a session; only `SKILL.md` and files a run opens are).
- One branch, `gauntlet-loop/next`. One commit per phase, message `gauntlet-loop: <outcome> – <one line>`. One pull request at the end, or one per phase if the user prefers review in smaller pieces; the plan does not depend on which.
- Nothing is deployed by this work. After the merge the operator refreshes the global mirror and installs hooks, agents and the allowlist into target repositories from the harness file's steps.

### 1.2 Ground rules for every phase

- Run mode stays usable: until phase 9 the workbench is the state and the prose rules in `running-the-loop.md` stand; phase 9 replaces the mechanism, not the rules.
- No harness claim without a dated verification line in `references/harness-claude-code.md`. Phase 0 creates that file as a fact list; phase 12 completes the quarantine.
- Every phase updates the README's rule ledger (rule, advisory or enforced, mechanism) for the rules it touches, and writes its decision entry in the existing shape: alternative, why, cost, evidence.
- The controller and hooks are stdlib Python, one file for the controller, one small script per hook, `unittest` for tests, no third-party packages, no framework. Simplicity is a requirement here, not a preference: a run may never edit tooling, so tooling must be small enough to trust.
- Nothing in the non-negotiables (spec §7.1) moves. A phase that touches one shows in its commit message which acceptance criterion proves it still holds.

### 1.3 Decisions to settle before their phase

Defaults apply if the user has not answered when the phase starts; the phase's commit message names the default it took.

| Concern | Needed by | Default |
| --- | --- | --- |
| C2 controller runtime | phase 7 | Python 3.11+ stdlib, single file |
| C7 envelope bootstrap values | phase 6 | local 60%, escalation 25%, whole-gate 15%; 10 invocations per piece; 1 hour per piece, 4-hour floor; write-mode default envelope 150 invocations and 24 hours when the user names none |
| C12 isolation required to execute reference code | phase 7 | keep the block |
| C6 deck row | phase 15 | remove the row |
| C1 attribution | phase 14 | follow the intent (credit both repositories) |
| C4 where the eval suite runs | phase 16 | GitHub Actions with a repository secret plus a local runner; branch protection on `main` |
| C10 `gauntlet-goal.md` | phase 20 | regenerate from the template |
| C3, C5, C11 | phase 0 spikes decide | see §3, phase 0 |

## 2. Phase map

| Phase | Intent outcome | Delivers | Depends on | Size |
| --- | --- | --- | --- | --- |
| 0 | none | baseline copied in, spikes recorded, eval cases as data, ledger skeleton | none | M |
| 1 | 1 blindness | five agent definitions, `critic_blind` hook, `.gauntlet/` layout, tier rules | 0 | M |
| 2 | 2 referent | per-piece referents, champion-challenger mode, bar refusals | 1 | S |
| 3 | 3 safety | `builder_boundary` and `protect_floors` hooks, invariants, `BLOCKED:` return, parking section | 1 | M |
| 4 | 4 states | seven states and transitions as prose, parking rules, parked-first report | 3 | S |
| 5 | 5 floors | DERIVED marking, findings to floors, `NOT REPRODUCED`, plan commit and attended gate | 4 | S |
| 6 | 14 stop | first line with second exit and different-model rule, envelope rules, terminal states | 5 | S |
| 7 | 15 untrusted | `gauntletctl` skeleton with `freeze`, `freeze-verify`, `scan`, `detect`; allowlist | 6 | M |
| 8 | 16 classes | failure class per entry, routing, scope failure as intent | 7 | S |
| 9 | 17 controller | state, events, machine, pair/swap, floors, attest, budgets, leases, projections, policy, `controller.md` | 8 | L |
| 10 | 6 cost | coarse-first, builder self-check, staged variants, prepare-once, specialists, conditional smoothing, `/effort xhigh` | 9 | M |
| 11 | 6b loading | `SKILL.md` write-mode only, `what-breaks.md`, trimmed run file, size checks | 10 | M |
| 12 | 7 harness | complete harness file, install steps, token grep | 11 | S |
| 13 | 8 write mode | third example, word-count check | 11 | S |
| 14 | 9 attribution | README credits | 0 | S |
| 15 | 10 loose ends | `design.md` pair prep, deck row, gate output | 9 | S |
| 16 | 11 tested | eval runner, critic pairs, baseline, CI workflow | 11, 13 | M |
| 17 | 12 pipeline | spec as input, commit set, PR, compliance, scope intent | 9 | S |
| 18 | 13 + table | full metrics, report fields, reading guide, mechanism table | 9 | M |
| 19 | example | `example-run.md` retold as an event log | 10–18 | M |
| 20 | release | ledger complete, all checks, folder swap, repo README, PR | all | S |

Sizes: S under half a day of focused work, M one to two days, L three to five days. They order the work; they are not promises.

## 3. Phases in detail

### Phase 0 – Baseline in, spikes, scaffolding

1. Create the branch. Copy `SKILL.md`, `README.md` and `references/` from `skills/gauntlet-loop` into this folder with `git cp` semantics (copy, then add). Move `intent.md`, `spec.md`, `plan.md` into `design/`.
2. Create a scratch target repository outside the project (the session scratch directory) with `.claude/settings.json`, `.claude/agents/`, a tiny fixture reference (a two-function JavaScript package that carries a `CLAUDE.md`, a `.env` and a `.cursor/` directory) and a git remote on disk. Every hook test, spike and later install test runs against it.
3. Run the spikes below. Each is a five-line experiment with a recorded result (date, Claude Code version, what was observed) in `references/harness-claude-code.md`, created in this phase as a dated fact list.

| Spike | Question | Decides |
| --- | --- | --- |
| S1 | Does an agent-scoped `PreToolUse` hook in a custom agent's frontmatter fire for `Read`, `Glob`, `Grep` and `Bash`, and does the payload carry `agent_id`, `agent_type`, `cwd`? Is `CLAUDE_PROJECT_DIR` set for the hook process? | phase 1 hook design |
| S2 | Do settings-level `SubagentStart` and `SubagentStop` fire for custom agents, match on agent type (`reader|reader-alt`), and carry the full last message and `transcript_path`? | phase 9 attest |
| S3 | Does `SubagentStop` fire when `maxTurns` is reached? | FR-17.12 collision guarantee |
| S4 | Is the hook command process sandboxed? Can it read a file under `sandbox.filesystem.denyRead` that the Bash tool cannot? | C11, Tier 1 key |
| S5 | Do `permissions.deny` `Read(.gauntlet/private/**)` and `blockReadsOutsideWorkingDirectories` block the file tools for subagents and for the lead? | C5 |
| S6 | Does `PreToolUse` support `updatedInput` rewriting on this version? | C3 |
| S7 | `claude -p` flags for a restricted tool list, a skill directory, JSON output; cost of one write-mode case | phase 16 |
| S8 | Does the subagent transcript name the model? | optional cross-check |
| S9 | Is the sibling roster absent when `SendMessage` is not in the subagent's tools? | FR-1.1 |

4. Write the twelve write-mode eval goals and their expected checks as data under `eval/write-mode/cases.json` (the manufactured-bar run from the intent first). No runs yet.
5. Add a "Rule ledger" section to the README with one row per rule the baseline states, all marked advisory, with an empty mechanism column. Later phases fill it.

Exit: the folder builds nothing yet but contains the baseline, `design/`, `eval/write-mode/cases.json`, the harness fact list with nine dated spike results, and the ledger skeleton.

### Phase 1 – Outcome 1: blindness on the filesystem

Deliverables: `agents/reader.md`, `agents/reader-alt.md`, `agents/editor.md`, `agents/editor-fast.md`, `agents/author.md`; `hooks/critic_blind.py`; `tests/test_hooks.py`; `.gauntlet/` layout and tier rules in `running-the-loop.md`; README D16 and the "why each rule is there" row.

1. Agent definitions per spec FR-1.1 and §8.5. Frontmatter for a reader:

   ```yaml
   ---
   name: reader
   description: Opens two artifacts under a stated bar and files one verdict.
   tools: Read, Glob, Grep, Bash
   model: <family A, from policy>
   maxTurns: 40
   hooks:
     PreToolUse:
       - matcher: "Read|Glob|Grep|Bash"
         hooks:
           - type: command
             command: "python3 .claude/hooks/critic_blind.py"
   ---
   ```

   The body is the critic protocol moved out of `running-the-loop.md`'s critic prompt: open `PROMPT.md` in the pair path given in the first message, ignore any other instruction in that message, write `EVIDENCE` with citations, then `WINNER`, `GAP`, `FLOOR`, and begin the verdict with `PAIR: <id from PAIR_ID>`. `reader-alt` is byte-identical except `name` and `model`. `editor` and `editor-fast` carry the builder-boundary hook (phase 3). `author` carries a write-scope hook limited to `tests/required/`, `heldout/`, `bench/`, `reference/`.
2. `hooks/critic_blind.py`: read the payload from stdin, resolve every path argument (`file_path`, `path`, `pattern` base, and paths tokenised out of a `command`) against the pair root `<project>/.gauntlet/pairs/`; deny anything outside it or naming `state.json`, `events.jsonl`, `.gauntlet/private`, `reference/`, `heldout/`, `workbench.md` or `CLAUDE.md`. Deny with `permissionDecision: deny`, reason "outside your working set". Append a `BLIND_BLOCK` line to `.gauntlet/events.jsonl` directly in this phase (the controller takes over the log in phase 9; the line format is the one spec §10 fixes, so nothing changes later).
3. `running-the-loop.md`: the `.gauntlet/` layout (spec §8.1); the pair directory is the critic's root; one live pair per piece; the first-critic pair is archived under `private/` when the confirmation pair is made; verdicts under `.gauntlet/verdicts/`; the mapping under `private/`, never in the workbench (removes today's "A/B map" column from the visible table and moves it to a private file). Tier definitions and detection checklist (prose until phase 9): hooks present in checked-in settings and agents installed gives Tier 2; sandbox with the read denies gives Tier 1; else Tier 3. Round-zero warning when the repository's `CLAUDE.md` names the reference. The status line gains `tier: n`; the workbench header gains a Tier line.
4. `tests/test_hooks.py`: payload fixtures for allow inside the pair; deny the workbench; deny `cat ../../state.json`; deny a Grep outside; deny a path that escapes with `..`.
5. README D16 (filesystem blindness; alternative: prompt only; cost: five definitions and a hook to maintain; evidence: the spikes). Why-table row. Ledger: blindness rules become "enforced when hooks checked in".

Checks: AC-1.2, AC-1.3 (wording: Tier 2 never says "isolated"), AC-1.4 now; AC-1.1 by hand in the scratch repo; AC-1.5 in phase 16.

### Phase 2 – Outcome 2: a referent per piece, or champion-challenger

1. `running-the-loop.md`: round zero assigns a referent per piece (new workbench column); a piece with no matching part in any reference runs champion-challenger: pair layout with an anchor `R` plus `A` and `B` for champion and challenger, the pick is which sits closer to `R`, confirmation swapped on `reader-alt`, convergence after two consecutive challenger losses plus a gap-only verdict naming no movable gap; report wording "converged against <referent>". Gap-only prompt variant written into `PROMPT.md` for that verdict.
2. `SKILL.md` Flow step 2: refuse by name a manufactured bar (a second build from the same spec) and a suite alone; offer per-piece referents; a goal with no referent for any piece is not a gauntlet, say so. "What breaks" gains the manufactured-bar entry.
3. README D17 (per-piece referents and champion-challenger; alternative: manufactured bar; cost: one extra artifact per verdict for those pieces; evidence: the motivating run).

Checks: AC-2.3 wording now; AC-2.1 by hand now, automated in phase 16; AC-2.2 in phase 13.

### Phase 3 – Outcome 3: the loop cannot wander

1. `hooks/builder_boundary.py` (agent-scoped, `editor` and `editor-fast`): deny `Edit`/`Write` outside the piece's worktree (the worktree root is the payload `cwd` for a builder working in it; until phase 9 the lead passes `GAUNTLET_WORKTREE` in the dispatch prompt and the hook falls back to the first path component under `wt/`), and to migrations, infrastructure, deploy configuration, `.env*`, secrets, `.claude/`, `.gauntlet/`; deny `Bash` matching deploy, publish, `git push`, migrate, `rm -rf` outside the worktree and package installs. Pattern lists live in the script until phase 9 moves them to `policy/v1.json`. The reason names the rule and says: return `BLOCKED: <reason>`.
2. `hooks/protect_floors.py` (settings-level): deny writes to `tests/required/`, `heldout/`, `reference/`, `bench/` and the eval set for every agent including the lead; exempt `agent_type == author` while `.gauntlet/ROUND_ZERO` exists (phase 9 replaces the marker with state), and any `gauntletctl floor` command.
3. `running-the-loop.md`: invariants extracted from "never" and "must not" phrases into the full bar sentence and the workbench; each command-checkable invariant registered as a floor; BUILDER prompt carries the boundary and the `BLOCKED:` return line; a `BLOCKED:` return parks the piece under open questions; hooks never prompt. Workbench gains a Parked section; status line gains `parked: n`.
4. `SKILL.md`: the one line under the prompt says the hooks must be checked in before the run for enforcement. Settings snippet for the hooks goes into the harness fact list (phase 12 turns it into install steps).
5. Tests: deny an edit to `heldout/x.mjs`; deny `git push origin main`; allow an edit inside the worktree; allow the author during round zero; deny the author after the marker is gone.
6. README D18. Ledger rows for floors and boundary: enforced when checked in.

Checks: AC-3.1, AC-3.2, AC-3.3.

### Phase 4 – Outcome 4: a stalled piece reaches a human

1. `running-the-loop.md`: the seven states as the workbench's state column; the legal transitions from spec §8.4.2 as a table (this table becomes `controller.md` in phase 9 unchanged); parking after the full ladder fails on the same gap; `PARKED` leaves only by a human resume, recorded under Escalations with the human named; the run is never ended by a parked piece; held-out floors run every round before any critic and again on every merge; report lists parked pieces first, each with its last verdict and one builder account.
2. README D19: reconcile parking with D2 (parking is per piece and never a judgment about the bar; the run's exits are unchanged).

Checks: AC-4.1 now; AC-4.2 in phase 9.

### Phase 5 – Outcome 5: floors are honest and grow from findings

1. `running-the-loop.md`: any floor the user did not supply is marked DERIVED in the workbench; a critic finding a command could have caught becomes a held-out test in that round, logged under Escalations with old and new floor and class `evaluation` (the class column arrives in phase 8; write it now as a word); builder alternative line `NOT REPRODUCED: <command and output>`; the lead reruns, and if it agrees the verdict is discarded, a fresh critic spawned, no gap routed; the workbench after round zero is the plan and is committed before any builder exists; attended runs stop there for approval; under `/goal` DERIVED items go under open questions and the run proceeds on stated assumptions.
2. README D20.

Checks: AC-5.1 in phase 19.

### Phase 6 – Outcome 14: a secure stop

1. `SKILL.md` prompt template, first line: "…the second with A and B swapped on a different model, pick ours on every piece and on the assembled whole, or N invocations or T hours are spent. Until then, run a gauntlet loop:". Write mode fills N and T from the user's budget, else from the write-mode default envelope (C7). Both filled examples updated; word counts stay under 270 (checked by hand now, by script in phase 13).
2. `running-the-loop.md`: the envelope (invocations counted per subagent spawn; wall-clock elapsed from the start on one clock); apportioning into local, escalation reserve and whole-gate reserve with the bootstrap proportions; per-piece allocation; a spent allocation enters the ladder like a repeated gap; no piece touches the whole-gate reserve; terminal states win, nothing left, ceiling; each writes the report and ends the lead's work; the status line carries `spent: i/N inv, h/T h` and, at the end, `ended: <state>`. Remove the "answer restarts with no tool call" clause. Keep "never write that the bar is out of reach".
3. Workbench template: envelope line and per-piece spend column.
4. README D21 (the cap is the exit; alternative: user-only stop; cost: a run can end below the bar; evidence: D2's own cost paragraph).

Checks: AC-14.1, AC-14.2 now; AC-14.3 in phase 9.

### Phase 7 – Outcome 15: the reference and the run are untrusted input

1. `bin/gauntletctl` skeleton: `#!/usr/bin/env python3`, argparse, sections `cli`, `fs`, `freeze`, `scan`, `detect`. Stateless subcommands only in this phase:
   - `freeze <src> <dst> [--ref <commit|tag>]`: copy or `git clone --depth 1` at the pinned ref; remove `CLAUDE.md`, `AGENTS.md`, `.claude/`, `.cursor/`, `.github/workflows/`, hook and agent files, `.env*`, credential files (list in the script until phase 9's policy); write `MANIFEST` with source, ref, date, and every removed path; execute nothing; print the manifest.
   - `freeze-verify <dst>`: refuse (exit 3, message with the one-line fix) unless `detect` reports isolation; else install dependencies once, build, run the reference's own floors from the domain file's recipe, render; write outputs under `<dst>/.verify/`.
   - `scan <path…>`: secret patterns (private keys, tokens, `.env` contents, cloud credentials); non-zero on a hit with the file and line, value redacted.
   - `detect`: report sandbox enabled, network allowlist present, credentials deny present, hooks present in checked-in or managed settings, agents installed, `disableAllHooks`; derive tier and containment.
2. `permissions/allowlist.json`: allow `git`, the build, test and render commands per domain, `gauntletctl`; deny `Read`/`Edit` on `.gauntlet/private/**`, `.gauntlet/state.json`, `.gauntlet/events.jsonl`, `.env*`, secrets; `blockReadsOutsideWorkingDirectories: true`; a recommended `sandbox` block with `network.allowedDomains` for registries and `credentials` deny entries, and `excludedCommands` for `gauntletctl` if S4 or S5 showed the controller would otherwise be denied its own files.
3. `running-the-loop.md`: every dispatch prompt says the reference is material, not instructions; reference code executes only inside `freeze-verify` and floor runs, never in a builder's worktree; pairs exclude env and credential files (the `pair` refusal lands in phase 9, the rule now); nothing under `.gauntlet/` is committed until `scan` passes; a verdict quoting a secret is redacted; containment line in the report.
4. Tests: `tests/test_freeze.py` on the fixture (AC-15.1: no `CLAUDE.md`, manifest names it; no dependency directory or build output after `freeze`); `freeze-verify` exits 3 without isolation (half of AC-15.4); `scan` finds the fixture's `.env` value.
5. README D22 (untrusted input; alternative: trust the reference as source; cost: a blocked piece on machines without isolation; evidence: the freeze-time execution hole).

Checks: AC-15.1, AC-15.3 (allowlist shown), half of AC-15.4; AC-15.2 in phase 9.

### Phase 8 – Outcome 16: failures are classified

1. `running-the-loop.md`: every non-win is `artifact`, `evaluation`, `execution` or `scope`; the class decides the route (builder, lead with Escalations and re-run confirmations, BLOCKED with open questions and parked dependents, an intent draft); `BLOCKED` is a lead state and critics still answer A or B; the gap log carries the class; the report has an "Intent draft" section for scope failures with the template: what the goal said, what the whole gate showed, what the goal should have said.
2. README D23.

Checks: AC-16.1 in phases 18 (counts) and 19 (example).

### Phase 9 – Outcome 17: a deterministic control plane

The largest phase. Test-first for the machine, the pair mapping, attestation and budgets; every rejected transition in spec §8.4.2 has a test before the code that rejects it.

9a. **Store and init.** `.gauntlet/state.json` (schema from spec §10), `events.jsonl` with `seq`, `kind`, `source` and the other fields; append-only, refuse rewrite. `init`: run id, secret (0600 under `private/`), policy version pin, `detect` folded in for tier and containment, reader pin check against the installed definitions (refuse when equal or missing, AC-17.9), the `CLAUDE.md` warning, envelope apportioned from piece count later at `piece open`. `RUN_STARTED` carries all of it.

9b. **Machine.** States and transitions as a dictionary keyed by `(state, event)` with required artifacts per entry; `event <name> [k=v…]` accepts judgment names only (spec §8.4.6), validates referenced facts (a `NOT_REPRODUCED_ACCEPTED` must name a `RERUN_OBSERVED`), applies the transition or exits non-zero with the rule. Derived facts (`GAP_REPEATED` from `GAP_SAME_AS_LAST`, `PIECE_PARKED` from a request or the ladder, `PIECE_OPENED` from `piece open`) are emitted by the controller. Tests: every rejected transition, every fact name through `event` (AC-17.2, AC-17.6).

9c. **Pair and swap.** Mapping seed `HMAC-SHA256(secret, run_id|piece|round)`; first bit picks which side is ours; `swap` inverts; mapping file under `private/mapping/`; `pair` copies ours into the live pair, strips names and loop traces (comments, filenames, commit messages matching the loop vocabulary), refuses on a `scan` hit (AC-15.2), writes `PROMPT.md` and `PAIR_ID` from the domain template, attaches the reference half prepared once by `pair --prepare` (matched module, adapter, reference floor outputs from `freeze-verify`), archives the first pair when `swap` runs, and opens the attempt record (`CRITIC_DISPATCHED` with expected type `reader` or `reader-alt`). Test: two runs of `pair` for the same inputs produce identical trees and mapping (AC-17.5).

9d. **Floors.** `floor add|amend|list` with the DERIVED flag and the command per floor; `floors <piece>` runs the lead-side floors on ours, writes outputs into the pair, emits `FLOOR_PASS` or `FLOOR_FAIL`; `amend` logs old and new and marks touched confirmations for re-run. `rerun <piece> <cmd>` records `RERUN_OBSERVED`.

9e. **Attest.** `attest --start` from `SubagentStart` registers `agent_id` and `agent_type` (`AGENT_REGISTERED`); `attest` from `SubagentStop` accepts a registered, not-yet-attested id whose type equals the open attempt's, a first line naming the live pair id, and a verdict of the right shape with at least one citation; records `CRITIC_RESULT` (or `BUILDER_DONE`, `SMOOTHER_DONE` by type), translates `WINNER` through the mapping into the derived verdict event, else `VERDICT_INVALID` with the reason. Model recorded from the pinned definition. Second attestation for one id: `ATTEST_CONFLICT`, both voided, derived transitions reverted, piece back to `ACTIVE`. Tier 1 key: the hook command passes `--key-file .gauntlet/private/attest.key` when S4 showed hook processes can read it; without a valid key at Tier 1, refuse. `hooks/register.py` and `hooks/attest.py` are thin wrappers that exec the controller. Tests: AC-17.7, AC-17.8 (both tiers), a builder line attested as `BUILDER_DONE`.

9f. **Budgets and leases.** Accounts and per-piece allocation per spec §8.4.3; a debit per spawn recorded with its event; `ALLOCATION_SPENT`; `BUDGET_EXHAUSTED` ends the run with the report; leases with owner, attempt and expiry, `status` emits `LEASE_EXPIRED`. Test: a scripted event stream with an unreachable bar and no named budget ends on the ceiling with the whole-gate reserve untouched until the gate (AC-14.3).

9g. **Projections and the rest.** `status` (the verbatim line; `--full` for resume), `workbench` (regenerate `.gauntlet/workbench.md` from state on every event), `next` (legal actions, each marked mechanical or judgment, with the event the lead must record), `gate` (the two whole-gate verdict paths and WINNER lines), `metrics` (the spec FR-13.1 set, completed in phase 18), `commit [--plan]` (scan, stage the committed set, commit), `promote` (`gh pr create` with the description template; `PR_OPENED`), `status` polling `gh pr view` for `PR_MERGED`, `resume` (human, logged with actor). `hooks/controller_only.py` (settings-level): deny writes to the state file, log, private storage and the controller's files, `git add|commit` touching `.gauntlet/` outside `gauntletctl commit`, and any tool invocation of `gauntletctl attest`.

9h. **Policy, docs, hand-over.** `policy/v1.json` with the fields in spec §8.4.5 and the C7 bootstrap values; the hook scripts read their pattern lists from it. `references/controller.md`: one page with states, events by class, the transition table, required artifacts, budget rules, escalation rules, authorities (AC-17.1). `running-the-loop.md`: the workbench becomes a projection the lead never edits; after compaction the lead runs `status --full`; the round-zero marker from phase 3 and the prose transition table from phase 4 are replaced by references to the controller. README D24 (bookkeeping in code; alternative: prose state; cost: a runtime and tests; evidence: the intent's own argument about mutable state in context).

Checks: AC-4.2, AC-14.3, AC-15.2, AC-17.1 through AC-17.9, AC-NN.1, AC-NN.5.

### Phase 10 – Outcome 6: consumption falls without touching the machinery

Text and small code changes, each with its own README entry stating the quality cost:

1. Coarse-first split in `SKILL.md` and round zero; shared state from a dependency graph when available, by rule for schema, migration, policy and config globs (policy file).
2. BUILDER prompt: run the required suite and return only when green, with the output; the lead runs held-out, hostile and benchmark.
3. Staged variants: `next` offers two variants first, a third only after both lose.
4. No idle turn boundaries: act on a return in the turn it arrives; a turn ends only when waiting on subagents.
5. `pair --prepare` once per piece at round zero (built in 9c; documented here); reference floors from `freeze-verify` attached once; ours once per round; the confirming critic gets the same files swapped; nothing re-rendered.
6. The lead's rerun of one cited command applies to wins only.
7. Specialists: `author` dispatch prompts for the floor author and the freezer; size thresholds in the policy file and in `running-the-loop.md` as numbers (reference beyond 12 files, floors beyond 60 lines, defaults to tune from metrics).
8. Builder briefs carry the matched module extract.
9. Conditional wave smoothing on `SHARED_EDGE_RECORDED`; rechecks only for judgment-visible diffs.
10. `example-run.md` read on a first run or an empty workbench only.
11. Write mode asks once for a budget with the bar pick; declines a loop for work too small for one; the line under the prompt says `/effort xhigh`.
12. Per-role effort in the agent definitions (`editor-fast`, `author` at `high`).

Checks: AC-6.1, AC-6.3 now; AC-6.2 in phase 19.

### Phase 11 – Outcome 6b: less is loaded

1. `SKILL.md`: frontmatter description cut to two lines; body holds write mode only (flow, the bar, the template, filling rules, length and voice, the examples, a one-paragraph pointer to run mode and to `what-breaks.md`); target 6 KB, ceiling 7 KB.
2. `references/what-breaks.md`: the "What breaks a gauntlet loop" rationale and the Portability detail.
3. `references/running-the-loop.md`: rules, dispatch prompts, workbench and report templates only; every "why" paragraph and the why-table move to the README; under 10 KB.
4. Run mode's default reading list: `running-the-loop.md`, one domain file, the harness file.
5. `eval/sizes.sh`: asserts the byte ceilings and the two-line description; runs in phase 16's CI.

Checks: AC-6b.1 now; AC-6b.2 in phase 16.

### Phase 12 – Outcome 7: harness facts are quarantined

1. Complete `references/harness-claude-code.md`: every fact from phase 0 with its date, every harness command the method needs (`/goal`, `/loop`, `/effort`, the concurrency variable, the Agent tool's `model` and `subagent_type`, `SendMessage` for resuming a builder, `wt` or `git worktree add`, `gh`), what to do when each is unavailable, and the install steps: copy `agents/*.md` into `.claude/agents/`, merge the hooks block into `.claude/settings.json`, merge `permissions/allowlist.json`, put `bin/` on PATH, enable the sandbox, check in, run `gauntletctl detect`.
2. Strip harness tokens from `SKILL.md` and every `references/` file except the harness file and the Portability section of `what-breaks.md`.
3. `eval/harness_tokens.sh`: greps the method files for the token list and fails on a hit (AC-7.1).
4. Fresh-clone test in the scratch repo: follow the install steps only, run `detect`, expect Tier 2 (AC-7.2).

### Phase 13 – Outcome 8: write mode refuses bad bars and shows the hard case

1. Third filled example in `SKILL.md`: a bespoke internal system with per-piece referents, one champion-challenger piece, a human-gate line, a budget clause.
2. `eval/wordcount.py`: counts the template and the three examples, fails above 270 (AC-NN.10, AC-8.2 by grep for the different-model rule and the second exit).

Checks: AC-8.1 by hand now and in phase 16; AC-2.2.

### Phase 14 – Outcome 9: attribution

Gate: C1. Default: follow the intent. README "Attribution" section credits both repositories and Shumer and names, per D-entry, which of their decisions this skill reversed. If the user keeps the earlier rule instead, the section stays as it is today and the ledger records the intent outcome as declined.

### Phase 15 – Outcome 10: loose ends

1. `domains/design.md`: pair preparation renders ours only; the reference render comes from `freeze-verify`.
2. Bar table: remove the deck row (C6 default).
3. `running-the-loop.md`: the whole-gate turn ends with pasted `gauntletctl gate` output.

### Phase 16 – Outcome 11: the skill is tested

1. `eval/run.sh`: for each write-mode case, `claude -p` with the skill directory loaded, tools restricted to none or read-only (from S7), JSON output captured to `eval/out/`; `eval/check.py` applies the case's checks (bar named and fetchable, exit line carries the different-model rule and the second exit, budget clause only when named, refusals by name, invariants present, under 270 words) and prints a pass rate.
2. `eval/critic/<domain>/`: three frozen pairs per domain (two clear, one near-tie) with a `PROMPT.md` each; `eval/run_critic.sh` dispatches a `reader` on each pair in both orders through `claude -p` and checks the WINNER line (known-better in both orders; a WINNER and no hedge on the near-tie).
3. `eval/baseline.json`: pass rates recorded from the first green run; `check.py` fails below them.
4. `.github/workflows/gauntlet-eval.yml` at the repository root (C4): path filters for the skill's `SKILL.md`, `references/`, `hooks/`, `agents/`, `policy/`, `eval/`; runs `sizes.sh`, `harness_tokens.sh`, `wordcount.py`, the controller tests, and the eval runner with the repository secret; a smoke subset for pull requests, the full suite on `main`.
5. AC-6b.2: one runner mode loads `SKILL.md` alone and expects the write-mode cases to pass.

Checks: AC-1.5, AC-2.1, AC-6b.2, AC-8.1, AC-11.1, AC-11.2, AC-12.1.

### Phase 17 – Outcome 12: the gauntlet fits the pipeline

1. Write mode accepts a `spec.md` or `intent.md` path: "never" and constraint sentences become invariants (up to three verbatim in the prompt, all in the workbench), acceptance criteria become DERIVED floors; the prompt names the file.
2. `commit` stages the committed set from spec §10 and nothing else; `promote` writes the PR description with links to the manifest, the workbench and the two whole-gate verdicts; `running-the-loop.md` says the PR's compliance pass checks the diff against the bar sentence and the two verdicts; `PROMOTED` only on `PR_MERGED` read from the remote.
3. Scope failure at the gate is written as an intent draft (phase 8 template), never a coherence piece.
4. README entry: what stays advisory (the skill's text) and what is enforced (hooks, branch protection, the controller).

Checks: AC-12.1 (phase 16), AC-12.3 now; AC-12.2 in phase 19.

### Phase 18 – Outcome 13 and the mechanism table

1. `metrics` completes the spec FR-13.1 set, including lead turns and tokens per confirmed piece separately from controller operations, worker-minutes, counts by failure class, and every value-column metric of the mechanism table; output as a table and as JSON.
2. Report template in `running-the-loop.md` gains the metric fields, the envelope, the tier, the containment line, parked-first ordering, the intent-draft section.
3. README: the mechanism table from the intent (five columns), the reading guide, the rule that a new mechanism enters only with all five columns and leaves only by a human reading three runs; `running-the-loop.md` states each mechanism's bound and exit where it is described. The README cost section says its estimate is replaced by measured numbers after three runs.

Checks: AC-13.2, AC-M.1 now; AC-13.1 and AC-16.1 in phase 19.

### Phase 19 – The example run as an event log

Rewrite `references/example-run.md` as the same duration-library run told through `gauntletctl` output: the paste prompt with the second exit; round zero with `init`, `freeze`, `freeze-verify`, the plan commit, one DERIVED floor, per-piece referents and one champion-challenger piece; a red floor; one `pair` per verdict and one `swap` per confirmation; a `NOT REPRODUCED` accepted; a finding converted to a held-out test; one failure of each class; a `BLOCKED` piece that clears; a parked piece; a compaction turn opened with `status --full`; the whole gate with `gate` output; `commit`, `promote`, the PR description; the report with every metric filled; the status line on every turn. Every line the harness would read is real controller output captured from a scripted event stream in `tests/fixtures/example-events.jsonl`, so the example cannot drift from the code (a test replays the stream and diffs the status lines against the document).

Checks: AC-5.1, AC-6.2, AC-10.3, AC-12.2, AC-13.1, AC-14.2, AC-16.1, AC-17.3, AC-17.4.

### Phase 20 – Release

1. README rule ledger complete: every rule the skill states, advisory or enforced, and the mechanism; every D-entry present (D16 onward), each earlier entry that changed rewritten in place with the new evidence.
2. Run the full acceptance list (spec §13) and record the result in the pull request description; `sizes.sh`, `harness_tokens.sh`, `wordcount.py`, the controller tests, the eval suite green.
3. Read `SKILL.md` alone in a fresh session and write one prompt from it; it must be correct without opening any reference.
4. Swap: `git rm -r skills/gauntlet-loop`, move this folder to `skills/gauntlet-loop`, update the skill row in the repository README, regenerate `slash-commands/gauntlet-goal.md` from the template (C10 default).
5. Open the pull request with the acceptance results and the ledger diff. After the merge, the operator refreshes the global mirror (`config/stack-init.sh global`) and installs into target repositories from the harness file.

## 4. Component design at file level

### 4.1 `bin/gauntletctl`

One Python file, sections in this order: `cli` (argparse, one subparser per command), `store` (load and save state with a lock file, append events with `seq`), `machine` (the transition table and `apply`), `budget`, `pair` (mapping, strip, copy, prompt), `floors`, `attest`, `freeze` (and verify, scan, detect), `projection` (status, workbench, gate, next), `metrics`, `git` (commit, promote, PR polling). Every command exits 0 on success, 2 on a rejected transition or invalid input, 3 on a refused precondition (no isolation, missing key, secret found). No global state outside `.gauntlet/`. The run secret is read once per invocation and never printed.

Skeleton of the state file (abridged from spec §10):

```json
{
  "run": {"id": "…", "policy": "v1", "tier": 2, "containment": {"sandbox": false, "network": false},
          "started": "…", "envelope": {"E": 150, "T_hours": 24}, "accounts": {"local": 90, "escalation": 37, "gate": 23}},
  "readers": {"reader": "<family A>", "reader-alt": "<family B>"},
  "pieces": {"parse": {"state": "ACTIVE", "kind": "piece", "referent": "…", "mode": "reference",
                       "allocation": 30, "spent": 4, "rung": 0, "lease": {"owner": "…", "attempt": "…", "expires": "…"},
                       "floors": [{"id": "heldout", "cmd": "…", "derived": true}], "last_gap": null, "verdicts": []}},
  "attempts": {"…": {"piece": "parse", "round": 2, "pair": "…", "expected_type": "reader", "status": "open"}},
  "invariants": [], "derived": [], "open_questions": [], "parked": []
}
```

### 4.2 Hooks

Each hook is a Python script that reads the payload from stdin, decides, and either exits 0 (allow, or with a JSON `permissionDecision: deny` object on stdout) or exits 2 with the reason on stderr. Pattern lists come from `policy/v1.json` after phase 9. Settings block installed into the target repository:

```json
{
  "hooks": {
    "PreToolUse": [
      {"matcher": "Edit|Write|Bash", "hooks": [
        {"type": "command", "command": "python3 .claude/hooks/protect_floors.py"},
        {"type": "command", "command": "python3 .claude/hooks/controller_only.py"}]}],
    "SubagentStart": [{"matcher": "reader|reader-alt|editor|editor-fast|author",
      "hooks": [{"type": "command", "command": "python3 .claude/hooks/register.py"}]}],
    "SubagentStop": [{"matcher": "reader|reader-alt|editor|editor-fast|author",
      "hooks": [{"type": "command", "command": "python3 .claude/hooks/attest.py"}]}]
  }
}
```

Agent-scoped hooks (`critic_blind`, `builder_boundary`, the author's write scope) live in the agent frontmatter, so they exist only while that agent runs.

### 4.3 Tests

`tests/` beside the controller: `test_machine.py`, `test_pair.py`, `test_attest.py`, `test_budget.py`, `test_hooks.py`, `test_freeze.py`, `test_example.py` (replays the example event stream). Fixtures under `tests/fixtures/`: the tiny reference package, sample verdicts in each shape (valid, no citation, WINNER first, hedge), a pair tree, the example event stream. Run with:

```bash
python3 -m unittest discover -s skills/gauntlet-loop/tests
```

### 4.4 Eval

`eval/write-mode/cases.json`, `eval/critic/<domain>/pair-N/`, `eval/run.sh`, `eval/run_critic.sh`, `eval/check.py`, `eval/sizes.sh`, `eval/harness_tokens.sh`, `eval/wordcount.py`, `eval/baseline.json`. Everything but the two `claude -p` runners is free and runs on every commit locally.

## 5. Verification matrix

| Acceptance group | Phase where it passes | How |
| --- | --- | --- |
| AC-NN.1, NN.5, 4.2, 14.3, 17.x | 9 | controller unit tests |
| AC-NN.10, 8.2, 14.1 | 13 | `wordcount.py` and grep |
| AC-1.1 | 1 | by hand in the scratch repo, recorded in the harness file |
| AC-1.2, 3.1, 3.2 | 1, 3 | hook unit tests and dispatch prompt grep |
| AC-1.3, 2.3, 4.1, 5.x wording | 1–5 | text review against the spec, recorded in the commit |
| AC-1.5, 2.1, 6b.2, 8.1, 11.x, 12.1 | 16 | eval suite |
| AC-6b.1 | 11 | `sizes.sh` |
| AC-7.1, 7.2 | 12 | `harness_tokens.sh`, fresh-clone install |
| AC-15.1, 15.2, 15.4 | 7, 9 | freeze, scan and pair tests |
| AC-5.1, 6.2, 10.3, 12.2, 13.1, 16.1, 17.3, 17.4 | 19 | example replay test |
| AC-M.1, 13.2, 12.3, 9.1, 10.1, 10.2, 6.1, 6.3 | 18, 17, 14, 15, 10 | README and file review |

## 6. Risks

| Risk | Mitigation |
| --- | --- |
| S4 fails: hook processes cannot read the key | Tier 1 attestation reported as Tier 2; C11's fallback (key in the managed hook command string) tried before that |
| S6 fails: no input rewriting | The reader's Bash check stays a deny by string match; the harness file recommends a container for Tier 1 |
| Double work between prose rules (phases 4–8) and the controller (phase 9) | Prose phases write the rule and a workbench column only; phase 9 replaces the mechanism, and the transition table is written once in phase 4 in the form `controller.md` keeps |
| Eval cost and credentials | Free checks on every commit; `claude -p` runs on `main` and on demand; the smoke subset for pull requests |
| Harness drift between phases | Dated facts; phase 20 re-runs the spikes that back an enforced rule before release |
| Size ceilings squeeze out something a prompt writer needs | AC-6b.2's `SKILL.md`-alone run is the guard; anything it fails on goes back into `SKILL.md` and something else leaves |
| "Same gap" is a judgment and could be gamed | It is a recorded judgment event; the escalation and flip metrics expose a lead that never calls a repeat |
| A real run during development picks up a half-built controller | Nothing is mirrored until phase 20; the baseline in `skills/gauntlet-loop` stays untouched until the swap |

## 7. Done

Every acceptance criterion in spec §13 passes and is recorded in the pull request; the README has an entry for every changed decision and a ledger row for every rule; the three examples and the example run reflect the new rules; the eval suite is green and wired to the skill's own paths; a fresh read of `SKILL.md` alone writes a correct prompt; and `skills/gauntlet-loop` is this folder.

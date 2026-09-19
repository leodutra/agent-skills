# Plan: gauntlet-loop

Status: implemented on branch `gauntlet-loop/next`, 2026-09-18; results in `acceptance.md`, deviations as spec amendments A9 to A11. Drafted for review and revised 2026-09-18 after a critique against the intent, the spec and the Claude Code docs as they read that day. Inputs: `intent.md` (the contract) and `spec.md` (requirements `FR-*`, acceptance criteria `AC-*`, concerns `C*`) beside this file. Baseline: `skills/gauntlet-loop` at commit 076dad3. Toolchain observed on 2026-09-10: Python 3.14, Node 26, `gh` 2.100, Claude Code 2.1.267, git 2.55. The plan needs Claude Code 2.1.271 or later (`omitClaudeMd`, and the handback behaviour spike S11 has to see); 2.1.274 was installed on 2026-09-18, so the floor is met and the harness file records it as the minimum. The repository has no CI directory. The global installer (`config/stack-init.sh`) mirrors a whole skill folder with `rm -rf` then `cp -R`, so everything the skill ships must live inside its folder.

The plan follows the intent's delivery order: outcomes 1, 2, 3, 4, 5, 14, 15, 16 (the holes), then 17 (the controller), then 6 and 6b (cost), then 7 to 13. Each outcome is one phase, one commit (phase 9: one per sub-phase), one README entry, and the skill is usable after every phase.

## 1. Strategy

### 1.1 Where the work happens

- The skill is changed in place, in `skills/gauntlet-loop`, on one branch, `gauntlet-loop/next`, checked out in its own worktree (`wt switch -c gauntlet-loop/next`). The main checkout stays on `main` and `config/stack-init.sh global` is only ever run from there, so no session can load a half-built skill. An earlier draft built the skill in a copy and swapped folders at the end; that forks the file history, leaves two skills named `gauntlet-loop` in the repository, misses any fix that lands on the baseline meanwhile, and makes every path written before the swap (the test command, the CI path filters) wrong after it.
- Phase 0 moves this folder to `skills/gauntlet-loop/design/` with `git mv`, so the ledger can link `intent.md`, `spec.md` and this plan and the mirror carries them (they are never loaded into a session; only `SKILL.md` and files a run opens are).
- One commit per phase, message `gauntlet-loop: <outcome> – <one line>`; phase 9 is one commit per sub-phase (9a to 9h), each green on its own tests. One pull request at the end, or one per phase if the user prefers review in smaller pieces; in place, a merged phase is a usable skill after a re-mirror, so the plan does not depend on which.
- Nothing is deployed by this work. After the merge the operator refreshes the global mirror and runs the installer (phase 1) in each target repository.

### 1.2 Ground rules for every phase

- Run mode stays usable: until phase 9 the workbench is the state and the prose rules in `running-the-loop.md` stand; phase 9 replaces the mechanism, not the rules.
- No harness claim without a dated verification line in `references/harness-claude-code.md`. Phase 0 creates that file as a fact list; phase 12 completes the quarantine.
- The spec is amended, never worked around. §1.4 lists the amendments this review found; the phase named there changes `design/spec.md` in the same commit. A phase that finds another hole does the same and says so in its commit message.
- A test arrives before the thing it guards. The write-mode eval runner and the word count exist from phase 0; every phase that changes what write mode says sees its own cases fail first, then pass.
- Every phase updates the README's rule ledger (rule, advisory or enforced, mechanism) for the rules it touches, and writes its decision entry in the existing shape: alternative, why, cost, evidence.
- The controller and hooks are stdlib Python, one file for the controller, one small script per hook, `unittest` for tests, no third-party packages, no framework. Simplicity is a requirement here, not a preference: a run may never edit tooling, so tooling must be small enough to trust.
- Hook commands are exec form with the project placeholder (`"command": "python3", "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/gauntlet/<hook>.py"]`), never a path relative to the working directory: a hook's working directory is wherever the agent last was.
- The event log has one writer. Hooks never append to `events.jsonl` themselves; on a deny they call `gauntletctl log-block`, which takes the lock, assigns `seq` and appends. It accepts the two block events and nothing else, so it cannot be used to forge a verdict; every other event reaches the log through the command that observed it. The controller file is born in phase 1 with that one subcommand and grows from there.
- Nothing in the non-negotiables (spec §7.1) moves. A phase that touches one shows in its commit message which acceptance criterion proves it still holds.

### 1.3 Decisions to settle before their phase

Defaults apply if the user has not answered when the phase starts; the phase's commit message names the default it took.

| Concern | Needed by | Default |
| --- | --- | --- |
| P1 install location in a target repository (new) | phase 1 | `.claude/hooks/gauntlet/` for the controller, the hooks, the policy and a hash manifest; `.claude/agents/` for the definitions. One directory, checked in, and write-protected by the sandbox natively |
| P2 worktree location (new) | phase 3 | `.gauntlet/wt/<piece>/`, inside the working directory. A sibling directory (worktrunk's default) is unwritable from sandboxed shell and unreadable under `blockReadsOutsideWorkingDirectories` |
| C2 controller runtime | phase 1 | Python 3.11+ stdlib, single file |
| C7 envelope bootstrap values | phase 6 | local 60%, escalation 25%, whole-gate 15%; 10 invocations per piece; 1 hour per piece, 4-hour floor; write-mode default envelope 150 invocations and 24 hours when the user names none |
| C12 isolation required to execute reference code | phase 7 | keep the block |
| C13 champion-challenger convergence rested on one critic (new, amendment A1) | decided 2026-09-18 by the user | The gap-only check runs twice: `reader` first, then `reader-alt` with the order swapped, and the piece converges only when both name no movable gap. No terminal claim in the method rests on one critic. Stricter than the intent's wording, so phase 2 amends outcome 2 and the champion-challenger row of the mechanism table in `design/intent.md` (exit: two fresh critics on different models name no movable gap; bound: one more invocation per converging piece) |
| C6 deck row | phase 15 | remove the row |
| C1 attribution | phase 14 | settled by the user 2026-09-19: credit Matt Shumer only; name no other implementation |
| C4 where the eval suite runs | phase 16 | GitHub Actions with a repository secret plus a local runner; branch protection on `main` |
| C10 `gauntlet-goal.md` | phase 20 | regenerate from the template |
| C3, C5, C11 | phase 0 spikes decide | see §3, phase 0, and the sandbox rule in phase 7 |

### 1.4 Spec amendments this plan carries

Holes found while planning. Each is committed to `design/spec.md` by the phase named.

| Id | Spec place | Amendment | Phase |
| --- | --- | --- | --- |
| A1 | §8.4.2, FR-2.3, FR-NN.3 | Champion-challenger has no path through the machine: `CONFIRMED` requires `CONFIRMATION_WIN`, a confirmed challenger win must return the piece to `ACTIVE` with a new champion, convergence has no event, and the gap-only verdict has no `WINNER` so the shape check voids it. Add: `CHAMPION_REPLACED` (derived from `CONFIRMATION_WIN` in this mode; to `ACTIVE`, loss counter reset), a loss counter, the gap-only verdict shape (`EVIDENCE`, then `GAP: <observation>` or `GAP: none`), `GAP_ONLY_RESULT`, and the confirmed form of convergence (C13): a first `GAP: none` from `reader` moves the piece to `AWAITING_CONFIRMATION`, a second from `reader-alt` on the swapped pair derives `CONVERGED` (to `CONFIRMED` with `mode: champion-challenger`), and a named gap from either returns it to `ACTIVE` with that gap routed. `CONVERGED` is the single exception to "no `CONFIRMED` without `CONFIRMATION_WIN`", and it carries the same two-reader, two-model requirement | 9b |
| A2 | §8.4.1 `pair`, FR-6.3 | The variants rung has no pair shape: the baseline's one critic over three variants plus the reference does not fit a two-sided pair with a one-bit mapping. Each variant is an ordinary pair against the reference, and a variant win is confirmed like any win; when every variant loses, one pair in the champion-challenger layout (anchor plus two of ours) picks which continues. No N-way pair ships | 9c |
| A3 | FR-3.3, FR-5.2, §8.4.1 `floor` | Floors cannot grow after round zero: the hook denies the lead and, after round zero, the author, and `floor add` has no way to receive a file. `floor add\|amend <id> --from <staged file> --cmd <command>` copies the file into the protected tree itself | 3 (interim), 9d |
| A4 | FR-3.2, §8.5 | Nothing stops a builder reading `heldout/` or `bench/`; the boundary covers edits only. `builder_boundary` also matches `Read\|Glob\|Grep` and denies those trees and `.gauntlet/` outside the agent's own worktree | 3 |
| A5 | FR-1.7, C9, §8.3 | Readers set `omitClaudeMd: true`, so the repository's `CLAUDE.md` no longer reaches a critic and C9 stops being a residual on a harness that supports it. The check for a `CLAUDE.md` naming the reference moves from `init` (which runs before the reference is known) to `freeze`, and lowers the tier only when the installed reader definitions lack the field | 1, 7 |
| A6 | FR-17.12, §8.4.6 | Single-use attestation would void every resumed builder: a builder keeps its context across rounds, so the same agent id stops once per round. Single use and collision voiding apply to readers; for editors a stop closes the open builder attempt (`PIECE_OPENED` and every `GAP_ROUTED` open one) and a stop with no open attempt is a note. The payload field is `agent_transcript_path`, and the verdict's source is decided by S11 | 9e |
| A7 | C5, C11, §8.5 allowlist | Excluding `gauntletctl` from the sandbox un-sandboxes `freeze-verify`, `floors` and `rerun`, the three commands that execute code the run does not trust, and hands the Tier 1 key to a lead-invoked `attest`. Replaced by the sandbox rule in phase 7 | 7 |
| A8 | §8.1 | Run-time layout gains `.gauntlet/.gitignore` (one line, `*`; `commit` stages the committed set with `git add -f` after the scan), `.gauntlet/wt/`, `.gauntlet/staging/`; package layout gains `install/claude_code.py`; installed layout per P1 | 1 |

## 2. Phase map

| Phase | Intent outcome | Delivers | Depends on | Size |
| --- | --- | --- | --- | --- |
| 0 | none | design docs moved in, scratch repo, fourteen spikes recorded, eval cases as data with the local write-mode runner and word count, ledger skeleton | none | L |
| 1 | 1 blindness | installer, five agent definitions, `critic_blind` hook, the log's single writer, `.gauntlet/` layout, tier rules | 0 | M |
| 2 | 2 referent | per-piece referents, champion-challenger mode, bar refusals | 1 | S |
| 3 | 3 safety | `builder_boundary` and `protect_floors` hooks, worktrees under `.gauntlet/wt/`, invariants, `BLOCKED:` return, parking section | 1 | M |
| 4 | 4 states | seven states and transitions as prose, parking rules, parked-first report | 3 | S |
| 5 | 5 floors | DERIVED marking, findings to floors, `NOT REPRODUCED`, plan commit and attended gate | 4 | S |
| 6 | 14 stop | first line with second exit and different-model rule, envelope rules, terminal states | 5 | S |
| 7 | 15 untrusted | `gauntletctl` grows `freeze`, `freeze-verify`, `scan`, `detect`; allowlist; the sandbox rule | 6 | M |
| 8 | 16 classes | failure class per entry, routing, scope failure as intent | 7 | S |
| 9 | 17 controller | state, events, machine, pair/swap, floors, attest, budgets, leases, projections, policy, `controller.md` | 8 | XL |
| 10 | 6 cost | coarse-first, builder self-check, staged variants, prepare-once, specialists, conditional smoothing, `/effort xhigh` | 9 | M |
| 11 | 6b loading | `SKILL.md` write-mode only, `what-breaks.md`, trimmed run file, size checks | 10 | M |
| 12 | 7 harness | complete harness file, install steps, token grep | 11 | S |
| 13 | 8 write mode | third example | 11 | S |
| 14 | 9 attribution | README credits | 0 | S |
| 15 | 10 loose ends | `design.md` pair prep, deck row, gate output | 9 | S |
| 16 | 11 tested | critic pairs, critic runner, baseline, CI workflow | 11, 13 | L |
| 17 | 12 pipeline | spec as input, commit set, PR, compliance, scope intent | 9 | S |
| 18 | 13 + table | full metrics, report fields, reading guide, mechanism table | 9 | M |
| 19 | example | `example-run.md` retold as an event log | 10–18 | L |
| 20 | release | ledger complete, all checks, repo README, PR | all | S |

Sizes: S under half a day of focused work, M one to two days, L three to five days, XL two to three weeks delivered as sub-commits. They order the work; they are not promises. Phase 9 is most of the code in the release, phase 16 is mostly authoring twenty-one frozen pairs, and phase 19 is a scripted run that has to exercise every rule.

## 3. Phases in detail

### Phase 0 – Docs in, spikes, test scaffolding

1. Create the branch in its own worktree. `git mv skills/gauntlet-loop-v2 skills/gauntlet-loop/design`. Record the installed Claude Code version (2.1.271 or later) as the first line of the harness fact list.
2. Create a scratch target repository outside the project (the session scratch directory) with `.claude/settings.json`, `.claude/agents/`, a tiny fixture reference (a two-function JavaScript package that carries a `CLAUDE.md`, a `.env` and a `.cursor/` directory) and a git remote on disk. Every hook test, spike and later install test runs against it.
3. Run the spikes below. Each is a five-line experiment with a recorded result (date, Claude Code version, what was observed) in `references/harness-claude-code.md`, created in this phase as a dated fact list. "Docs" is what the Claude Code docs said on 2026-09-18; a spike confirms it on the installed version or overturns it.

| Spike | Question | Decides |
| --- | --- | --- |
| S1 | Does an agent-scoped `PreToolUse` hook in a custom agent's frontmatter fire for `Read`, `Glob`, `Grep` and `Bash`, in exec form with `${CLAUDE_PROJECT_DIR}`, and does the payload carry `agent_id` and `agent_type`? | phase 1 hook design |
| S2 | Do settings-level `SubagentStart` and `SubagentStop` fire for custom agents, match on agent type (`reader\|reader-alt`), and carry the full last message and `agent_transcript_path`? | phase 9 attest |
| S3 | Does `SubagentStop` fire when `maxTurns` is reached? Docs: the output comes back marked partial and the agent can be resumed | FR-17.12 collision guarantee |
| S4 | Is the hook command process sandboxed? Can it read a file under `sandbox.filesystem.denyRead` that the Bash tool cannot? Docs: hooks run outside the sandbox | C11, Tier 1 key |
| S5 | Do `permissions.deny` `Read(.gauntlet/private/**)` and `blockReadsOutsideWorkingDirectories` block the file tools for subagents and for the lead? | C5 |
| S6 | Does `PreToolUse` support `updatedInput` rewriting on this version? | C3 |
| S7 | `claude -p` flags for a restricted tool list, a skill directory, JSON output, a pinned model; does `claude -p --agent reader` run a definition as the main agent with its frontmatter hooks live; cost of one write-mode case and one critic case | step 4, phase 16, C4 |
| S8 | Does the subagent transcript name the model and carry token usage? Does a lead `Stop` hook see the lead's? | optional cross-check; phase 18 token metrics |
| S9 | Is the sibling roster absent when `SendMessage` is not in the subagent's tools? | FR-1.1 |
| S10 | What `cwd` does a `PreToolUse` payload carry for a subagent that ran `cd` into a worktree? Docs: a subagent starts in the lead's directory and its `cd` does not persist, so expect the project root | phase 3 binding rule |
| S11 | On 2.1.271 or later, does a reader with a `tools:` allowlist deliver its verdict in `last_assistant_message`, or through the handback tool (then `tool_input.message` of a hook matched on that tool)? | phase 9e input, A6 |
| S12 | A builder resumed with `SendMessage`: same `agent_id`? Do `SubagentStart` and `SubagentStop` fire again? | A6 |
| S13 | A reader with `omitClaudeMd: true` asked to quote a canary line from the scratch repo's `CLAUDE.md`: absent? | A5, C9 |
| S14 | Under the sandbox: is `.gauntlet/wt/<piece>/` writable from sandboxed shell; can a sandboxed `gauntletctl` read `.gauntlet/private/` under a `denyRead`; does `excludedCommands` match a subcommand prefix (`gauntletctl pair *`); does a compound command containing an excluded prefix run unsandboxed? | the sandbox rule, A7, P2 |

4. Eval scaffolding, local only. `eval/write-mode/cases.json`: the twelve write-mode goals and their expected checks as data (the manufactured-bar run from the intent first), each with a `phase` number, the phase that must turn it green. `eval/run.sh [--upto n]` runs the cases through `claude -p` with the flags S7 found; `eval/check.py` applies the checks; `eval/wordcount.py` counts the template and every filled example and fails above 270. Run all three against the baseline and record which cases already pass.
5. Add a "Rule ledger" section to the README with one row per rule the baseline states, all marked advisory, with an empty mechanism column. Later phases fill it.

Exit: the skill is unchanged in behaviour and contains `design/`, the eval cases with a runner that works, the harness fact list with fourteen dated spike results, and the ledger skeleton.

### Phase 1 – Outcome 1: blindness on the filesystem

Deliverables: `install/claude_code.py`; `agents/reader.md`, `agents/reader-alt.md`, `agents/editor.md`, `agents/editor-fast.md`, `agents/author.md`; `hooks/critic_blind.py`; `hooks/_paths.py`; `bin/gauntletctl` with `log-block` only; `tests/test_hooks.py`, `tests/test_install.py`; `.gauntlet/` layout and tier rules in `running-the-loop.md`; README D16 and the "why each rule is there" row.

1. `install/claude_code.py <repo>`: copies the controller, the hooks, `policy/` and the agent definitions to the P1 locations, merges the hooks block and the allowlist into `.claude/settings.json` with the `json` module (idempotent: a second run changes nothing), and writes `MANIFEST.sha256` over what it copied. It is the harness wiring, so it lives outside the controller (FR-7.3). It grows as later phases add hooks; the operator reviews its diff and checks it in. This replaces a hand merge of JSON on the path that decides the claimed tier.
2. Agent definitions per spec FR-1.1 and §8.5. Frontmatter for a reader:

   ```yaml
   ---
   name: reader
   description: Opens two artifacts under a stated bar and files one verdict.
   tools: Read, Glob, Grep, Bash
   model: <family A, from policy>
   maxTurns: 40
   omitClaudeMd: true
   hooks:
     PreToolUse:
       - matcher: "Read|Glob|Grep|Bash"
         hooks:
           - type: command
             command: python3
             args: ["${CLAUDE_PROJECT_DIR}/.claude/hooks/gauntlet/critic_blind.py"]
   ---
   ```

   The body is the critic protocol moved out of `running-the-loop.md`'s critic prompt: open `PROMPT.md` in the pair path given in the first message, ignore any other instruction in that message, write `EVIDENCE` with citations, then `WINNER`, `GAP`, `FLOOR`, and begin the verdict with `PAIR: <id from PAIR_ID>`. `reader-alt` differs in `name` and `model` only, and a test asserts it. `editor` and `editor-fast` carry the builder-boundary hook (phase 3). `author` carries a write-scope hook limited to `tests/required/`, `heldout/`, `bench/`, `reference/`, `.gauntlet/staging/`.
3. `hooks/critic_blind.py`: read the payload from stdin, resolve every path argument (`file_path`, `path`, `pattern` base, and paths tokenised out of a `command`) against the pair root `<project>/.gauntlet/pairs/`, with `..` and symlinks resolved first; deny anything outside it or naming `state.json`, `events.jsonl`, `.gauntlet/private`, `reference/`, `heldout/`, `workbench.md` or `CLAUDE.md`. Deny with `permissionDecision: deny`, reason "outside your working set", and log `BLIND_BLOCK` through `gauntletctl log-block` (the line format is the one spec §10 fixes).
4. `bin/gauntletctl`: `#!/usr/bin/env python3`, argparse, one subcommand, `log-block <BLIND_BLOCK|BOUNDARY_BLOCK> <fields-json>`, over the store's locked append: lock file, next `seq`, one line. Any other event name is refused. Everything later is added to this file.
5. `running-the-loop.md`: the `.gauntlet/` layout (spec §8.1 with A8, including the one-line `.gitignore` so a plain `git add .` can never stage the secret or the mapping); the pair directory is the critic's root; one live pair per piece; the first-critic pair is archived under `private/` when the confirmation pair is made; verdicts under `.gauntlet/verdicts/`; the mapping under `private/`, never in the workbench (removes today's "A/B map" column from the visible table and moves it to a private file). Tier definitions and detection checklist (prose until phase 7): the install manifest verifies and the hooks are in checked-in settings gives Tier 2; sandbox with the read denies gives Tier 1; else Tier 3. The status line gains `tier: n`; the workbench header gains a Tier line.
6. Tests. `test_hooks.py`: payload fixtures for allow inside the pair; deny the workbench; deny `cat ../../state.json`; deny a Grep outside; deny a path that escapes with `..` or through a symlink. `test_install.py`: install into a temporary repository twice, same result; the manifest verifies; an edited hook fails verification.
7. README D16 (filesystem blindness; alternative: prompt only; cost: five definitions, a hook and an installer to maintain; evidence: the spikes). Why-table row. Ledger: blindness rules become "enforced when installed and checked in".

Checks: AC-1.2, AC-1.3 (wording: Tier 2 never says "isolated"), AC-1.4 now; AC-1.1 by hand in the scratch repo; AC-1.5 in phase 16.

### Phase 2 – Outcome 2: a referent per piece, or champion-challenger

1. Eval first: the manufactured-bar case, the suite-alone case and the two no-referent cases fail against the current text.
2. `running-the-loop.md`: round zero assigns a referent per piece (new workbench column); a piece with no matching part in any reference runs champion-challenger: pair layout with an anchor `R` plus `A` and `B` for champion and challenger, the pick is which sits closer to `R`, confirmation swapped on `reader-alt`, a confirmed challenger becomes the champion and the piece continues, convergence after two consecutive challenger losses plus two gap-only verdicts naming no movable gap, the second on `reader-alt` with the order swapped (C13); report wording "converged against <referent>". Gap-only prompt variant written into `PROMPT.md` for that verdict, with its own verdict shape (A1).
3. `SKILL.md` Flow step 2: refuse by name a manufactured bar (a second build from the same spec) and a suite alone; offer per-piece referents; a goal with no referent for any piece is not a gauntlet, say so. "What breaks" gains the manufactured-bar entry.
4. README D17 (per-piece referents and champion-challenger; alternative: manufactured bar; cost: one extra artifact per verdict for those pieces; evidence: the motivating run).

Checks: AC-2.1 and AC-8.1 by the local runner now, in CI from phase 16; AC-2.3 wording now; AC-2.2 in phase 13.

### Phase 3 – Outcome 3: the loop cannot wander

1. Worktrees live at `.gauntlet/wt/<piece>/` (P2), created with `git worktree add`; from phase 9 `piece open` creates them. `running-the-loop.md` and the harness fact list say so.
2. `hooks/builder_boundary.py` (agent-scoped, `editor` and `editor-fast`, matcher `Read|Glob|Grep|Edit|Write|Bash`). The payload cannot say which worktree is the agent's (S10), so the hook binds on first write: an agent's first `Edit` or `Write` under `.gauntlet/wt/<piece>/` records `agent_id → piece` in `.gauntlet/private/bindings/`, and every later write must resolve inside that worktree. The wave and the whole are smoothed in worktrees of their own under the same root, so the smoother binds the same way. Inside it, deny migrations, infrastructure, deploy configuration, `.env*`, secrets, `tests/required/`. Outside it, deny every write. Deny reads of `heldout/`, `bench/` and `.gauntlet/` outside the bound worktree (A4). Deny `Bash` matching deploy, publish, `git push`, migrate, `rm -rf` outside the worktree and package installs. Protected trees match as path segments (`hooks/_paths.py`, shared with `protect_floors`), so the copy of `tests/required/` inside a worktree is covered. Pattern lists live in the script until phase 9 moves them to `policy/v1.json`. The reason names the rule and says: return `BLOCKED: <reason>`. Blocks are logged as `BOUNDARY_BLOCK` through `log-block`.
3. `hooks/protect_floors.py` (settings-level): deny writes to `tests/required/`, `heldout/`, `reference/`, `bench/` and the eval set for every agent including the lead; exempt `agent_type == author`. Until phase 9 the exemption is not limited to round zero, because phase 5 needs a new held-out test mid-run and the only agent allowed to write one is an author the lead dispatches (A3); 9d narrows it to round zero once `floor add --from` exists.
4. `running-the-loop.md`: invariants extracted from "never" and "must not" phrases into the full bar sentence and the workbench; each command-checkable invariant registered as a floor; BUILDER prompt carries the boundary and the `BLOCKED:` return line; a `BLOCKED:` return parks the piece under open questions; hooks never prompt. Workbench gains a Parked section; status line gains `parked: n`.
5. `SKILL.md`: the one line under the prompt says the hooks must be installed and checked in before the run for enforcement. The installer gains the two hooks.
6. Tests: deny an edit to `heldout/x.mjs`; deny a read of it from an editor; deny `git push origin main`; allow an edit inside the bound worktree; deny an edit in a second worktree after binding; deny `tests/required/` inside the worktree; allow the author.
7. README D18. Ledger rows for floors and boundary: enforced when installed and checked in.

Checks: AC-3.1, AC-3.2, AC-3.3.

### Phase 4 – Outcome 4: a stalled piece reaches a human

1. `running-the-loop.md`: the seven states as the workbench's state column; the legal transitions from spec §8.4.2 as a table (this table becomes `controller.md` in phase 9, plus A1's rows); parking after the full ladder fails on the same gap; `PARKED` leaves only by a human resume, recorded under Escalations with the human named; the run is never ended by a parked piece; held-out floors run every round before any critic and again on every merge; report lists parked pieces first, each with its last verdict and one builder account.
2. README D19: reconcile parking with D2 (parking is per piece and never a judgment about the bar; the run's exits are unchanged).

Checks: AC-4.1 now; AC-4.2 in phase 9.

### Phase 5 – Outcome 5: floors are honest and grow from findings

1. `running-the-loop.md`: any floor the user did not supply is marked DERIVED in the workbench; a critic finding a command could have caught becomes a held-out test in that round, written by an `author` the lead dispatches (the lead itself is denied the tree), logged under Escalations with old and new floor and class `evaluation` (the class column arrives in phase 8; write it now as a word); builder alternative line `NOT REPRODUCED: <command and output>`; the lead reruns, and if it agrees the verdict is discarded, a fresh critic spawned, no gap routed; the workbench after round zero is the plan and is committed before any builder exists; attended runs stop there for approval; under `/goal` DERIVED items go under open questions and the run proceeds on stated assumptions.
2. README D20.

Checks: AC-5.1 in phase 19.

### Phase 6 – Outcome 14: a secure stop

1. Eval first: every case now expects the second exit and the different-model rule in the first line, and `wordcount.py` runs on the template and both examples.
2. `SKILL.md` prompt template, first line: "…the second with A and B swapped on a different model, pick ours on every piece and on the assembled whole, or N invocations or T hours are spent. Until then, run a gauntlet loop:". Write mode fills N and T from the user's budget, else from the write-mode default envelope (C7). Both filled examples updated.
3. `running-the-loop.md`: the envelope (invocations counted per subagent spawn; wall-clock elapsed from the start on one clock); apportioning into local, escalation reserve and whole-gate reserve with the bootstrap proportions; per-piece allocation; a spent allocation enters the ladder like a repeated gap; no piece touches the whole-gate reserve; terminal states win, nothing left, ceiling; each writes the report and ends the lead's work; the status line carries `spent: i/N inv, h/T h` and, at the end, `ended: <state>`. Remove the "answer restarts with no tool call" clause. Keep "never write that the bar is out of reach". One compatibility line (spec §6): a pasted baseline prompt without the second exit or the different-model rule still runs, and the lead applies the policy defaults for both.
4. Workbench template: envelope line and per-piece spend column.
5. README D21 (the cap is the exit; alternative: user-only stop; cost: a run can end below the bar; evidence: D2's own cost paragraph).

Checks: AC-14.1, AC-14.2, AC-8.2, AC-NN.10 now; AC-14.3 in phase 9.

### Phase 7 – Outcome 15: the reference and the run are untrusted input

1. `bin/gauntletctl` gains sections `fs`, `freeze`, `scan`, `detect`. Stateless subcommands only in this phase:
   - `freeze <src> <dst> [--ref <commit|tag>]`: copy or `git clone --depth 1` at the pinned ref; remove `CLAUDE.md`, `AGENTS.md`, `.claude/`, `.cursor/`, `.github/workflows/`, hook and agent files, `.env*`, credential files (list in the script until phase 9's policy); write `MANIFEST` with source, ref, date, and every removed path; execute nothing; print the manifest. It also runs the FR-1.7 check, since it is the first command that knows the reference's name (A5): grep the repository's `CLAUDE.md` files for that name and the loop vocabulary, and report whether a reader could see the text (the installed reader definitions lack `omitClaudeMd`).
   - `freeze-verify <dst>`: refuse (exit 3, message with the one-line fix) unless `detect` reports isolation and its own probe agrees: it tries to create and delete a file in the project's parent directory, and refuses if that succeeds, so a wrong `detect` or an exclusion somebody added cannot un-isolate it. Else install dependencies once, build, run the reference's own floors from the domain file's recipe, render; write outputs under `<dst>/.verify/`.
   - `scan <path…>`: secret patterns (private keys, tokens, `.env` contents, cloud credentials); non-zero on a hit with the file and line, value redacted.
   - `detect`: report sandbox enabled, network allowlist present, credentials deny present, hooks present in checked-in or managed settings, the install manifest verifying (a hook that exists but was edited is not Tier 2), agents installed with `omitClaudeMd`, `disableAllHooks`; derive tier and containment. The settings paths and key names it reads sit in one table at the top of the section and are mirrored in the harness file, so the controller's knowledge of the harness is one screen (FR-7.3).
2. The sandbox rule (A7, settles C5 and C11 with S4 and S14). `freeze-verify`, `floors` and `rerun` execute code the run does not trust: they never appear in `excludedCommands` and never read private storage. If a Tier 1 read deny on `.gauntlet/private/` stops the lead-invoked controller reading its own secret, only the non-executing subcommands are excluded, by pattern (`init`, `pair`, `swap`, `gate`, `commit`), and only if S14 showed patterns match per subcommand and compound commands do not ride along. `attest` is never excluded: the hook process reads the key because hooks run outside the sandbox, and a lead-invoked `attest` cannot, which is the whole of Tier 1 origin authentication. If S14 says the split cannot be made, the read deny on private storage is dropped, private storage stays behind the permission denies and `controller_only`, and the run reports Tier 2 (C11's fallback). This is also the first thing cut if phase 9 runs long.
3. `permissions/allowlist.json`: allow `git`, the build, test and render commands per domain, the controller by its installed path; deny `Read`/`Edit` on `.gauntlet/private/**`, `.gauntlet/state.json`, `.gauntlet/events.jsonl`, `.env*`, secrets; `blockReadsOutsideWorkingDirectories: true`; a recommended `sandbox` block with `network.allowedDomains` for registries, `credentials` deny entries, `allowUnsandboxedCommands: false`, and the exclusion patterns from step 2 when they apply.
4. `running-the-loop.md`: every dispatch prompt says the reference is material, not instructions; reference code executes only inside `freeze-verify` and floor runs, never in a builder's worktree; pairs exclude env and credential files (the `pair` refusal lands in phase 9, the rule now); nothing under `.gauntlet/` is committed until `scan` passes; a verdict quoting a secret is redacted; containment line in the report.
5. Tests: `tests/test_freeze.py` on the fixture (AC-15.1: no `CLAUDE.md`, manifest names it; no dependency directory or build output after `freeze`); `freeze-verify` exits 3 without isolation, and exits 3 when `detect` is forced to say "isolated" but the probe write succeeds; `scan` finds the fixture's `.env` value; `detect` reports Tier 3 for a tampered hook.
6. README D22 (untrusted input; alternative: trust the reference as source; cost: a blocked piece on machines without isolation; evidence: the freeze-time execution hole).

Checks: AC-15.1, AC-15.3 (allowlist shown), the first half of AC-15.4; AC-15.2 and the second half of AC-15.4 in phase 9.

### Phase 8 – Outcome 16: failures are classified

1. `running-the-loop.md`: every non-win is `artifact`, `evaluation`, `execution` or `scope`; the class decides the route (builder, lead with Escalations and re-run confirmations, BLOCKED with open questions and parked dependents, an intent draft); `BLOCKED` is a lead state and critics still answer A or B; the gap log carries the class; the report has an "Intent draft" section for scope failures with the template: what the goal said, what the whole gate showed, what the goal should have said.
2. README D23.

Checks: AC-16.1 in phases 18 (counts) and 19 (example).

### Phase 9 – Outcome 17: a deterministic control plane

The largest phase, most of the release's code. One commit per sub-phase, each with its tests green. Test-first for the machine, the pair mapping, attestation and budgets; every rejected transition in spec §8.4.2 has a test before the code that rejects it. The spec amendments A1, A2, A3 and A6 are committed with the sub-phase that implements them.

9a. **Store and init.** `events.jsonl` with `seq`, `kind`, `source` and the other fields; append-only, refuse rewrite, the locked append from phase 1 is the only path in. `.gauntlet/state.json` (schema from spec §10) is a cache: state is the fold of the log through one pure function, `apply(state, event)`, and `load` rebuilds the cache when it is missing or behind. Unit tests, AC-14.3's scripted stream, phase 19's replay and conflict voiding all use that function, so nothing ever needs to push a fact event through the CLI. `init`: run id, secret (0600 under `private/`), `.gauntlet/.gitignore`, policy version pin, `detect` folded in for tier and containment, reader pin check against the installed definitions (refuse when equal or missing, AC-17.9), envelope apportioned from piece count later at `piece open`. `RUN_STARTED` carries all of it.

9b. **Machine.** States and transitions as a dictionary keyed by `(state, event)` with required artifacts per entry, including A1's champion-challenger rows; `event <name> [k=v…]` accepts judgment names only (spec §8.4.6), validates referenced facts (a `NOT_REPRODUCED_ACCEPTED` must name a `RERUN_OBSERVED`), applies the transition or exits non-zero with the rule. Derived facts (`GAP_REPEATED` from `GAP_SAME_AS_LAST`, `PIECE_PARKED` from a request or the ladder, `PIECE_OPENED` from `piece open`, `CHAMPION_REPLACED` and `CONVERGED` in champion-challenger mode) are emitted by the controller. `piece open` also creates the worktree under `.gauntlet/wt/`. Tests: every rejected transition, every fact name through `event` (AC-17.2, AC-17.6), a champion-challenger piece from open to `CONFIRMED`, `CONVERGED` rejected outside that mode, and `CONVERGED` rejected when the second gap-only verdict is missing or came from `reader`.

9c. **Pair and swap.** Mapping seed `HMAC-SHA256(secret, run_id|piece|round)`; first bit picks which side is ours (in the champion-challenger layout, which of `A` and `B` is the challenger, beside the anchor `R`); `swap` inverts; mapping file under `private/mapping/`; `pair` copies ours into the live pair, strips names and loop traces (comments, filenames, commit messages matching the loop vocabulary), refuses on a `scan` hit (AC-15.2), writes `PROMPT.md` and `PAIR_ID` from the domain template (`--gap-only` writes the gap-only variant over the champion and `R`, and `swap` inverts their order for the second reader), attaches the reference half prepared once by `pair --prepare` (matched module, adapter, reference floor outputs from `freeze-verify`), archives the first pair when `swap` runs, and opens the attempt record (`CRITIC_DISPATCHED` with expected type `reader` or `reader-alt`). The variants rung uses these two layouts and nothing else (A2). Test: two runs of `pair` for the same inputs produce identical trees and mapping (AC-17.5).

9d. **Floors.** `floor add|amend <id> --from <staged file> --cmd <command> [--derived]` copies the staged file from `.gauntlet/staging/` into the protected tree and registers it (A3); `amend` logs old and new and marks touched confirmations for re-run; `floor list`. `protect_floors` now exempts the author during round zero only, read from state, and the marker-free interim of phase 3 goes. `floors <piece>` runs the lead-side floors on ours, writes outputs under `.gauntlet/floors/<piece>/r<n>/` (floors run before the round's pair exists, and this command never reads the mapping; `pair` copies them into our side), emits `FLOOR_PASS` or `FLOOR_FAIL`; when a floor needs the reference to execute and the run has no isolation it records `PIECE_BLOCKED` with class `execution` (second half of AC-15.4, tested with detection stubbed both ways). `rerun <piece> <cmd>` records `RERUN_OBSERVED`.

9e. **Attest.** `attest --start` from `SubagentStart` registers `agent_id` and `agent_type` (`AGENT_REGISTERED`). `attest` from `SubagentStop` takes the agent's final text from the source S11 established. For readers: accept a registered, not-yet-attested id whose type equals the open attempt's, a first line naming the live pair id, and a verdict of the right shape (pairwise or gap-only, as the attempt says) with at least one citation; record `CRITIC_RESULT`, translate `WINNER` through the mapping into the derived verdict event, else `VERDICT_INVALID` with the reason; a second attestation for one reader id is `ATTEST_CONFLICT`: one event naming both `seq` numbers, which the fold skips from then on, so the piece is back in `ACTIVE` without rewriting the log. For editors (A6): the agent is tied to its piece by the phase 3 binding, a stop closes that piece's open builder attempt as `BUILDER_DONE` (or `SMOOTHER_DONE`), and a stop with no open attempt is a note, never a conflict, because a resumed builder stops once per round by design. Model recorded from the pinned definition. Tier 1 key: the hook command passes `--key-file .gauntlet/private/attest.key`; it authenticates only under phase 7's sandbox rule, and without it the run reports Tier 2 attestation. `hooks/register.py` and `hooks/attest.py` are thin wrappers that exec the controller. Tests: AC-17.7, AC-17.8 (both tiers), a builder attested across two rounds on one agent id.

9f. **Budgets and leases.** Accounts and per-piece allocation per spec §8.4.3; a debit per spawn recorded with its event; `ALLOCATION_SPENT`; `BUDGET_EXHAUSTED` ends the run with the report; leases with owner, attempt and expiry, `status` emits `LEASE_EXPIRED`. Test: a scripted event stream with an unreachable bar and no named budget ends on the ceiling with the whole-gate reserve untouched until the gate (AC-14.3).

9g. **Projections and the rest.** `status` (the verbatim line; `--full` for resume; it also bumps a lead-turn counter in state, since the lead ends every turn on it), `workbench` (regenerate `.gauntlet/workbench.md` from state on every event), `next` (legal actions, each marked mechanical or judgment, with the event the lead must record), `gate` (the two whole-gate verdict paths and WINNER lines), `metrics` (the spec FR-13.1 set, completed in phase 18), `commit [--plan]` (scan, `git add -f` the committed set, commit), `promote` (`gh pr create` with the description template; `PR_OPENED`), `status` polling `gh pr view` for `PR_MERGED`, `resume` (human, logged with actor). `hooks/controller_only.py` (settings-level): deny writes to the state file, log, private storage, the installed controller directory and the agent definitions, `git add|commit` touching `.gauntlet/` outside `gauntletctl commit`, and any tool invocation of `gauntletctl attest`.

9h. **Policy, docs, hand-over.** `policy/v1.json` with the fields in spec §8.4.5 and the C7 bootstrap values; the hook scripts read their pattern lists from the installed copy beside them. `references/controller.md`: one page with states, events by class, the transition table, required artifacts, budget rules, escalation rules, authorities (AC-17.1). `running-the-loop.md`: the workbench becomes a projection the lead never edits; after compaction the lead runs `status --full`; the prose transition table from phase 4 is replaced by a reference to the controller. README D24 (bookkeeping in code; alternative: prose state; cost: a runtime and tests; evidence: the intent's own argument about mutable state in context).

Checks: AC-4.2, AC-14.3, AC-15.2, AC-15.4 (second half), AC-17.1, AC-17.2, AC-17.5 through AC-17.9, AC-NN.1, AC-NN.5.

### Phase 10 – Outcome 6: consumption falls without touching the machinery

Text and small code changes, each with its own README entry stating the quality cost:

1. Coarse-first split in `SKILL.md` and round zero; shared state from a dependency graph when available, by rule for schema, migration, policy and config globs (policy file).
2. BUILDER prompt: run the required suite and return only when green, with the output; the lead runs held-out, hostile and benchmark.
3. Staged variants: `next` offers two variants first, a third only after both lose, judged in the two pair layouts of 9c (A2).
4. No idle turn boundaries: act on a return in the turn it arrives; a turn ends only when waiting on subagents.
5. `pair --prepare` once per piece at round zero (built in 9c; documented here); reference floors from `freeze-verify` attached once; ours once per round; the confirming critic gets the same files swapped; nothing re-rendered.
6. The lead's rerun of one cited command applies to wins only.
7. Specialists: `author` dispatch prompts for the floor author and the freezer; size thresholds in the policy file and in `running-the-loop.md` as numbers (reference beyond 12 files, floors beyond 60 lines, defaults to tune from metrics).
8. Builder briefs carry the matched module extract.
9. Conditional wave smoothing on `SHARED_EDGE_RECORDED`; rechecks only for judgment-visible diffs.
10. `example-run.md` read on a first run or an empty workbench only.
11. Write mode asks once for a budget with the bar pick; declines a loop for work too small for one (eval case first); the line under the prompt says `/effort xhigh`.
12. Per-role effort in the agent definitions (`editor-fast`, `author` at `high`).

Checks: AC-6.1, AC-6.3 now; AC-6.2 in phase 19.

### Phase 11 – Outcome 6b: less is loaded

1. Guard first: `eval/run.sh --skill-only` loads `SKILL.md` with `references/` hidden and must pass every write-mode case before and after this phase (AC-6b.2). This is the only thing that says whether the cut removed something a prompt writer needs, so it runs here, not five phases later.
2. `SKILL.md`: frontmatter description cut to two lines; body holds write mode only (flow, the bar, the template, filling rules, length and voice, the examples, a one-paragraph pointer to run mode and to `what-breaks.md`); target 6 KB, ceiling 7 KB.
3. `references/what-breaks.md`: the "What breaks a gauntlet loop" rationale and the Portability detail.
4. `references/running-the-loop.md`: rules, dispatch prompts, workbench and report templates only; every "why" paragraph and the why-table move to the README; under 10 KB.
5. Run mode's default reading list: `running-the-loop.md`, one domain file, the harness file.
6. `eval/sizes.sh`: asserts the byte ceilings and the two-line description; runs in phase 16's CI.

Checks: AC-6b.1, AC-6b.2 now by the local runner; both in CI from phase 16.

### Phase 12 – Outcome 7: harness facts are quarantined

1. Complete `references/harness-claude-code.md`: every fact from phase 0 with its date and the minimum harness version, every harness command the method needs (`/goal`, `/loop`, `/effort`, the concurrency variable, the Agent tool's `model` and `subagent_type`, `SendMessage` for resuming a builder, `git worktree add` under `.gauntlet/wt/`, `gh`), what to do when each is unavailable, and the install steps: run `install/claude_code.py <repo>`, review the diff, enable the sandbox, check in, run `gauntletctl detect`.
2. Strip harness tokens from `SKILL.md` and every `references/` file except the harness file and the Portability section of `what-breaks.md`.
3. `eval/harness_tokens.sh`: greps the method files for the token list and fails on a hit (AC-7.1).
4. Fresh-clone test in the scratch repo, scripted: follow the install steps only, run `detect`, expect Tier 2 (AC-7.2).

### Phase 13 – Outcome 8: write mode refuses bad bars and shows the hard case

1. Third filled example in `SKILL.md`: a bespoke internal system with per-piece referents, one champion-challenger piece, a human-gate line, a budget clause. `wordcount.py` (phase 0) covers it; the `SKILL.md` size ceiling from phase 11 still holds with it in.

Checks: AC-8.1, AC-8.2, AC-NN.10, AC-2.2.

### Phase 14 – Outcome 9: attribution

Gate: C1, settled by the user on 2026-09-19. README "Attribution" credits Matt Shumer for the method and nothing else; the alternatives this skill decided against are listed unnamed, each with its D-entry.

Checks: AC-9.1.

### Phase 15 – Outcome 10: loose ends

1. `domains/design.md`: pair preparation renders ours only; the reference render comes from `freeze-verify`.
2. Bar table: remove the deck row (C6 default).
3. `running-the-loop.md`: the whole-gate turn ends with pasted `gauntletctl gate` output.

Checks: AC-10.1, AC-10.2 now; AC-10.3 in phase 19.

### Phase 16 – Outcome 11: the skill is tested

The write-mode runner has existed since phase 0; this phase adds the critic side and makes the suite a gate.

1. `eval/critic/<domain>/`: three frozen pairs per domain (two clear, one near-tie) with a `PROMPT.md` each; `eval/run_critic.sh` runs a `reader` on each pair in both orders (`claude -p --agent reader` if S7 showed the definition's hooks stay live that way, else a one-line lead prompt that dispatches it) and checks the WINNER line (known-better in both orders; a WINNER and no hedge on the near-tie).
2. A gate that does not flake. Both runners pin model ids, so a harness upgrade never reads as a skill regression. `eval/baseline.json` records the lowest pass rate of three consecutive runs; `check.py` fails below it. A single stochastic miss on a twelve-case suite would otherwise block every merge or teach everyone to re-run until green.
3. `.github/workflows/gauntlet-eval.yml` at the repository root (C4): path filters for `skills/gauntlet-loop/` (`SKILL.md`, `references/`, `hooks/`, `agents/`, `policy/`, `bin/`, `install/`, `eval/`); runs `sizes.sh`, `harness_tokens.sh`, `wordcount.py`, the controller tests, and both eval runners with the repository secret, in full, on every pull request the filters match. The filters are what bound the cost; a smoke subset on pull requests would mean the full suite fails only after the merge, which is not FR-11.3. If S7's measured cost makes the full suite on pull requests unacceptable, C4 picks the subset and the ledger records FR-11.3 as enforced for that subset only.
4. Branch protection on `main` requires the workflow.

Checks: AC-1.5, AC-11.1, AC-11.2; AC-2.1, AC-6b.2, AC-8.1, AC-12.1 now also in CI.

### Phase 17 – Outcome 12: the gauntlet fits the pipeline

1. Write mode accepts a `spec.md` or `intent.md` path (eval case first): "never" and constraint sentences become invariants (up to three verbatim in the prompt, all in the workbench), acceptance criteria become DERIVED floors; the prompt names the file.
2. `commit` stages the committed set from spec §10 and nothing else; `promote` writes the PR description with links to the manifest, the workbench and the two whole-gate verdicts; `running-the-loop.md` says the PR's compliance pass checks the diff against the bar sentence and the two verdicts; `PROMOTED` only on `PR_MERGED` read from the remote.
3. Scope failure at the gate is written as an intent draft (phase 8 template), never a coherence piece.
4. README entry: what stays advisory (the skill's text) and what is enforced (hooks, branch protection, the controller).

Checks: AC-12.1, AC-12.3 now; AC-12.2 in phase 19.

### Phase 18 – Outcome 13 and the mechanism table

1. `metrics` completes the spec FR-13.1 set: counts by failure class, every value-column metric of the mechanism table, worker-minutes from `AGENT_REGISTERED` to the stop, lead turns from the counter `status` keeps (9g), reported separately from controller operations. Tokens per confirmed piece are read from the transcripts the stop hooks name if S8 found usage there, and printed as `n/a` otherwise; the spec asks for them only "where the harness exposes usage". Output as a table and as JSON.
2. Report template in `running-the-loop.md` gains the metric fields, the envelope, the tier, the containment line, parked-first ordering, the intent-draft section.
3. README: the mechanism table from the intent (five columns), the reading guide, the rule that a new mechanism enters only with all five columns and leaves only by a human reading three runs; `running-the-loop.md` states each mechanism's bound and exit where it is described. The README cost section says its estimate is replaced by measured numbers after three runs.

Checks: AC-13.2, AC-M.1 now; AC-13.1 and AC-16.1 in phase 19.

### Phase 19 – The example run as an event log

Rewrite `references/example-run.md` as the same duration-library run told through `gauntletctl` output: the paste prompt with the second exit; round zero with `init`, `freeze`, `freeze-verify`, the plan commit, one DERIVED floor, per-piece referents and one champion-challenger piece that converges; a red floor; one `pair` per verdict and one `swap` per confirmation; a `NOT REPRODUCED` accepted; a finding converted to a held-out test through `floor add --from`; one failure of each class; a `BLOCKED` piece that clears; a parked piece; a builder resumed across two rounds; a compaction turn opened with `status --full`; the whole gate with `gate` output; `commit`, `promote`, the PR description; the report with every metric filled; the status line on every turn. Every line the harness would read is real controller output: the event stream lives in `tests/fixtures/example-events.jsonl`, a test folds it through `apply` (9a) and diffs the status lines against the document, so the example cannot drift from the code.

Checks: AC-5.1, AC-6.2, AC-10.3, AC-12.2, AC-13.1, AC-14.2, AC-16.1, AC-17.3, AC-17.4.

### Phase 20 – Release

1. README rule ledger complete: every rule the skill states, advisory or enforced, and the mechanism; every D-entry present (D16 onward), each earlier entry that changed rewritten in place with the new evidence.
2. Re-run the spikes that back an enforced rule on the then-current harness version and re-date them. Run the full acceptance list (spec §13) and record the result in the pull request description; `sizes.sh`, `harness_tokens.sh`, `wordcount.py`, the controller tests, the eval suite green.
3. Read `SKILL.md` alone in a fresh session and write one prompt from it; it must be correct without opening any reference.
4. Update the skill row in the repository README; regenerate `slash-commands/gauntlet-goal.md` from the template (C10 default). There is no folder swap: the work was in place.
5. Open the pull request with the acceptance results, the ledger diff and the spec amendments. After the merge, the operator refreshes the global mirror (`config/stack-init.sh global`) from the main checkout and runs the installer in target repositories.

## 4. Component design at file level

### 4.1 `bin/gauntletctl`

One Python file, sections in this order: `cli` (argparse, one subparser per command), `store` (one locked append with `seq`, `log-block` its only direct CLI door; `load` as the fold of the log, `state.json` as its cache), `machine` (the transition table and the pure `apply`), `budget`, `pair` (mapping, strip, copy, prompt, the two layouts), `floors`, `attest`, `freeze` (and verify with its probe, scan, detect with its harness table), `projection` (status, workbench, gate, next), `metrics`, `git` (commit, promote, PR polling). Every command exits 0 on success, 2 on a rejected transition or invalid input, 3 on a refused precondition (no isolation, missing key, secret found). No global state outside `.gauntlet/`. The run secret is read once per invocation and never printed. In a target repository it is installed at `.claude/hooks/gauntlet/gauntletctl` and called by that path; this plan and the method files write `gauntletctl` for short.

Skeleton of the state file (abridged from spec §10):

```json
{
  "run": {"id": "…", "policy": "v1", "tier": 2, "containment": {"sandbox": false, "network": false},
          "started": "…", "envelope": {"E": 150, "T_hours": 24}, "accounts": {"local": 90, "escalation": 37, "gate": 23},
          "lead_turns": 0},
  "readers": {"reader": "<family A>", "reader-alt": "<family B>"},
  "pieces": {"parse": {"state": "ACTIVE", "kind": "piece", "referent": "…", "mode": "reference",
                       "worktree": ".gauntlet/wt/parse", "champion": null, "challenger_losses": 0,
                       "allocation": 30, "spent": 4, "rung": 0, "lease": {"owner": "…", "attempt": "…", "expires": "…"},
                       "floors": [{"id": "heldout", "cmd": "…", "derived": true}], "last_gap": null, "verdicts": []}},
  "attempts": {"…": {"piece": "parse", "round": 2, "pair": "…", "expected_type": "reader", "shape": "pairwise", "status": "open"}},
  "voided": [], "invariants": [], "derived": [], "open_questions": [], "parked": []
}
```

### 4.2 Hooks

Each hook is a Python script that reads the payload from stdin, decides, and either exits 0 (allow, or with a JSON `permissionDecision: deny` object on stdout) or exits 2 with the reason on stderr. Path resolution (`..`, symlinks, path segments) is one function in `hooks/_paths.py`, imported by every deny hook and tested once. Pattern lists come from the installed `policy/v1.json` after phase 9. Settings block the installer merges into the target repository:

```json
{
  "hooks": {
    "PreToolUse": [
      {"matcher": "Edit|Write|Bash", "hooks": [
        {"type": "command", "command": "python3", "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/gauntlet/protect_floors.py"]},
        {"type": "command", "command": "python3", "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/gauntlet/controller_only.py"]}]}],
    "SubagentStart": [{"matcher": "reader|reader-alt|editor|editor-fast|author",
      "hooks": [{"type": "command", "command": "python3", "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/gauntlet/register.py"]}]}],
    "SubagentStop": [{"matcher": "reader|reader-alt|editor|editor-fast|author",
      "hooks": [{"type": "command", "command": "python3", "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/gauntlet/attest.py"]}]}]
  }
}
```

Agent-scoped hooks (`critic_blind`, `builder_boundary`, the author's write scope) live in the agent frontmatter, so they exist only while that agent runs.

### 4.3 Tests

`tests/` beside the controller: `test_machine.py`, `test_pair.py`, `test_attest.py`, `test_budget.py`, `test_hooks.py`, `test_install.py`, `test_freeze.py`, `test_example.py` (replays the example event stream). Fixtures under `tests/fixtures/`: the tiny reference package, sample verdicts in each shape (valid, no citation, WINNER first, hedge, gap-only with and without a gap), a pair tree in each layout, the example event stream. Run with:

```bash
python3 -m unittest discover -s skills/gauntlet-loop/tests
```

### 4.4 Eval

`eval/write-mode/cases.json`, `eval/critic/<domain>/pair-N/`, `eval/run.sh`, `eval/run_critic.sh`, `eval/check.py`, `eval/sizes.sh`, `eval/harness_tokens.sh`, `eval/wordcount.py`, `eval/baseline.json`. Everything but the two `claude -p` runners is free and runs on every commit locally; the write-mode runner runs locally before and after every phase that changes what write mode says.

## 5. Verification matrix

| Acceptance group | Phase where it passes | How |
| --- | --- | --- |
| AC-NN.1, NN.5, 4.2, 14.3, 17.1, 17.2, 17.5–17.9 | 9 | controller unit tests; `controller.md` size check |
| AC-NN.10, 8.2, 14.1 | 6, again in 13 | `wordcount.py` and grep |
| AC-1.1 | 1 | by hand in the scratch repo, recorded in the harness file |
| AC-1.2, 3.1, 3.2 | 1, 3 | hook unit tests and dispatch prompt grep |
| AC-1.3, 2.3, 4.1, 5.x wording | 1–5 | text review against the spec, recorded in the commit |
| AC-1.4, 3.3, 14.2, 15.3 | 1, 3, 6, 7 | README and template review; `status` output in 9 |
| AC-2.1, 8.1, 12.1 | 2, 13, 17 | local write-mode runner; in CI from 16 |
| AC-2.2 | 13 | the third example, by grep |
| AC-6b.1, 6b.2 | 11 | `sizes.sh`; `run.sh --skill-only` |
| AC-1.5, 11.1, 11.2 | 16 | critic runner; workflow file and branch protection |
| AC-7.1, 7.2 | 12 | `harness_tokens.sh`, scripted fresh-clone install |
| AC-15.1, 15.4 (first half) | 7 | freeze and probe tests |
| AC-15.2, 15.4 (second half) | 9c, 9d | pair refusal test; `floors` with detection stubbed both ways; one sandboxed run by hand in the scratch repo |
| AC-5.1, 6.2, 10.3, 12.2, 13.1, 16.1, 17.3, 17.4 | 19 | example replay test |
| AC-M.1, 13.2, 12.3, 9.1, 10.1, 10.2, 6.1, 6.3 | 18, 17, 14, 15, 10 | README and file review |

Every criterion in spec §13 appears in one row.

## 6. Risks

| Risk | Mitigation |
| --- | --- |
| S4 or S14 fails: hook processes cannot read the key, or the sandbox cannot tell executing subcommands from the rest | Phase 7's sandbox rule already names the fallback: Tier 1 attestation reported as Tier 2. Commands that execute untrusted code stay sandboxed in every branch of that rule |
| S6 fails: no input rewriting | The reader's Bash check stays a deny by string match; the harness file recommends a container for Tier 1 |
| S11 or S12 overturn the attestation input (handback tool, resumed ids) | Both are spiked in phase 0, before any attest code; A6 is written for either answer |
| Double work between prose rules (phases 4–8) and the controller (phase 9) | Prose phases write the rule and a workbench column only; phase 9 replaces the mechanism, and the transition table is written once in phase 4 in the form `controller.md` keeps |
| Phase 9 is most of the release and could stall it | Sub-commits 9a–9h, each usable by the tests of the next; cut order if it runs long: Tier 1 key handling, then token metrics; nothing in §7.1 depends on either |
| Eval cost, credentials and flakiness | Free checks on every commit; pinned models; baseline is the lowest of three runs; path filters bound the paid runs |
| Harness drift between phases | Dated facts with a minimum version; phase 20 re-runs the spikes that back an enforced rule before release |
| Size ceilings squeeze out something a prompt writer needs | `run.sh --skill-only` runs before and after the cut in phase 11; anything it fails on goes back into `SKILL.md` and something else leaves |
| "Same gap" is a judgment and could be gamed | It is a recorded judgment event; the escalation and flip metrics expose a lead that never calls a repeat |
| A real session picks up the half-built skill | The branch lives in its own worktree; the mirror is refreshed only from the main checkout on `main` |
| A spec hole found mid-phase gets patched in code only | Ground rule: the spec changes in the same commit; the pull request lists every amendment |

## 7. Done

Every acceptance criterion in spec §13 passes and is recorded in the pull request; `design/spec.md` carries amendments A1 to A8 and any found later; the README has an entry for every changed decision and a ledger row for every rule; the three examples and the example run reflect the new rules; the eval suite is green, stable across three runs and wired to the skill's own paths; a fresh read of `SKILL.md` alone writes a correct prompt; and `skills/gauntlet-loop` is the skill this plan describes.

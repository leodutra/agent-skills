# Specification: gauntlet-loop

Status: draft for review. Input: `intent.md` beside this file. Baseline inspected: `skills/gauntlet-loop` at commit 076dad3 (`SKILL.md`, `README.md`, `references/running-the-loop.md`, `references/example-run.md`, seven `references/domains/` files) and `slash-commands/gauntlet-goal.md`. Harness facts were checked against the Claude Code docs on 2026-09-10; §14 lists what was verified and what was not.

Requirement ids are `FR-<outcome>.<n>` and acceptance criteria `AC-<outcome>.<n>`, where `<outcome>` is the numbered outcome in `intent.md` (`NN` for the non-negotiables, `M` for the mechanism table). §17 is the index.

## 1. Overview

The skill stays what it is: a Claude Code skill that writes a short paste-ready gauntlet prompt (write mode) or runs the loop as lead (run mode) against a frozen real reference, with fresh blind critics, swapped-order cross-model confirmation, command floors, an escalation ladder and an assembled-whole gate.

This release closes the edges the intent names, and does it with three kinds of change:

1. **Enforcement.** Every rule that must always hold gets a deterministic mechanism behind it: subagent definitions with tool allowlists, PreToolUse hooks, a controller that owns state and legal transitions, branch protection on the run's PR.
2. **A control plane.** Bookkeeping leaves the lead's prose and moves into `gauntletctl`, a shipped deterministic controller: state file, append-only event log, fixed state machine, pinned policy, budget escrow, leases, seeded idempotent pair preparation, verdict provenance attested by the harness, metrics.
3. **Less spent.** Fewer pieces and rounds, work done once per piece instead of once per round, mechanical steps scripted, specialists off the lead, less text loaded per session.

The deliverable is one skill folder that replaces `skills/gauntlet-loop`, containing: `SKILL.md` (write mode), `README.md` (decision ledger), `references/` (run mode, controller contract, one dated harness file, domain files, an example run retold as an event log), `bin/gauntletctl`, `policy/`, `hooks/`, `agents/`, `permissions/`, `eval/` and the controller's tests.

## 2. Problem and desired outcome

**Problem.** The method is the most rigorous of its kind on the critic side and weakest at its edges. Blindness holds in the prompt but not on the filesystem. A piece with no fetchable referent has no mode. Nothing stops the loop from touching a migration or a deploy. A stalled piece never reaches a human. The lead invents floors with no flag. Harness facts are spread through the method. Cost is paid as fixed overhead per piece and per critic. Bookkeeping lives in the lead's context, the most expensive place for it. A real run manufactured a bar from a second build of the same spec, passed a floor that tested nothing the critic later found, and the skill said nothing was wrong.

**Desired outcome.** After this change: a critic cannot reach anything but its pair; every piece has a referent or a declared mode; builders cannot leave scope; stalled pieces park and the run continues; derived floors are marked and grow from findings; the run has a hard ceiling it does not grade; the reference is treated as untrusted input; every non-win has a class and an owner; a controller keeps state and says what is legally next; the run reports its own numbers; the skill is tested on every change; and the whole loads less text and spends fewer invocations for the same exits.

**Unchanged.** Everything in §7.1. The strength of a check never varies at run time (§7.2).

## 3. Scope

### 3.1 In scope

- Every outcome 1 through 17 of `intent.md`, plus the mechanism table and the delivery order.
- The controller, its tests, hooks, agent definitions, policy file, permission allowlist and eval suite, all shipped inside the skill folder.
- README entries for every changed decision, the rule ledger (advisory or enforced), the mechanism table, the metrics reading guide, attribution.
- Rewrites of `SKILL.md`, `references/running-the-loop.md`, `references/example-run.md`, the domain files' pair-preparation lines, and the three filled examples.
- `slash-commands/gauntlet-goal.md`: updated so it does not contradict the new rules (second exit, different-model rule in the first line, parked count).

### 3.2 Out of scope

- Changing what a win is, how many critics judge it, how strong they are, or when confirmation runs (§7.2).
- A scheduler model, budget model, or any second model with authority over the run.
- Adapting the skill to harnesses other than Claude Code beyond the existing Portability text; the controller is harness-agnostic by design but only the Claude Code wiring ships.
- `skills/security-vuln-gauntlet`: untouched.
- Deploying the finished skill into `~/.claude/skills` and into target repos' `.claude/`; the harness file documents the steps, the release does not run them.
- A domain file for "Deck, doc, deliverable" (§16, C6). The default is to drop the row.

### 3.3 Assumptions

- The harness facts in §14.1 hold at run time; each is dated in `references/harness-claude-code.md` and re-verified before a release that touches it.
- Runs happen in a git repository with a remote that supports pull requests and branch protection (`gh` available). Without one, outcome 12's promotion step is reported as not applied, and the run still ends with a report.
- A target repository checks the skill's hooks and agent definitions into `.claude/` before a run, or the run reports every hook-backed rule as advisory.
- Python 3.11 or later is on PATH for the controller (§16, C2 if a different runtime is chosen).

### 3.4 Dependencies

- Claude Code with custom subagents, agent-scoped hooks, `/goal`, `/effort`, permission rules, and optionally the Bash sandbox (§14.1).
- `git`, `gh`, and the per-domain tools the existing domain files already require (Playwright, axe-core, Lighthouse, hyperfine, and so on).
- A held-out API credential for the eval suite in CI (§16, C4).

## 4. Users and stakeholders

| Who | Uses | Needs from this change |
| --- | --- | --- |
| The operator (the user) | Write mode in any session; run mode on a goal; the README | A prompt that refuses bad bars; a run that cannot wander, cannot self-certify, and ends on its own; a report with parked pieces first; numbers to read across runs |
| The lead (an agent in run mode) | `running-the-loop.md`, one domain file, the harness file, `gauntletctl` | A controller that tells it what is legal next; nothing to bookkeep; small context |
| Builders, critics, the smoother, the floor author, the freezer | Their dispatch prompt and their agent definition | Tool limits that match their role; blocks that explain themselves |
| The PR reviewer | The run's PR and committed artifacts | Manifest, bar sentences, workbench, verdicts, report, and a compliance pass against the bar sentence |
| The skill's maintainer | README ledger, eval suite, controller tests | A green suite before merge; one entry per decision; metrics that say which mechanisms earn their cost |

## 5. Functional requirements

Each requirement is observable. Where the template fields (actor, trigger, precondition, behaviour, resulting state, failure) add information they are given; otherwise the statement carries them.

### FR-NN. Non-negotiables (unchanged behaviour that must be shown to still hold)

- **FR-NN.1** The bar is named, fetchable, comparable and frozen by the lead before any builder is spawned. Controller: `PIECE_OPENED` for a builder-bearing piece is rejected while the run has no `REFERENCE_FROZEN` event.
- **FR-NN.2** A critic is a fresh subagent per verdict. It never receives the reference's name, builder notes, history, or which side is ours. Enforced by the `reader` agent definition and hook (FR-1.x); the emitted critic prompt contains no such text (eval, FR-11.x).
- **FR-NN.3** Verdicts are pairwise. `EVIDENCE` precedes `WINNER`. One `GAP`, stated as an observation. No ties; a hedge is a loss. A verdict violating the shape, or citing nothing it opened or ran, is `VERDICT_INVALID` and discarded; the controller applies the shape check and translates `WINNER` through the mapping it holds (FR-17.12).
- **FR-NN.4** Command floors run by the lead (through the controller) before any critic. A red floor ends the round: `FLOOR_FAIL` makes `pair` refuse for that piece and round.
- **FR-NN.5** Every win is confirmed by a second fresh critic on a different model with the order swapped, not re-flipped. Losses are not confirmed. `CONFIRMED` without a `CONFIRMATION_WIN` carrying a different model id is rejected.
- **FR-NN.6** A repeated gap escalates (split, fresh builder, variants) and never lowers the bar or ends the loop. There is no round count and no "no improvement, stop". The only bounds are the resource ceilings (FR-14).
- **FR-NN.7** The lead owns authorship and custody of tests, held-out sets and eval splits: it specifies them, reviews them, and is the only agent that may amend them, through the controller. A disposable `author` may implement the files from the lead's brief (outcome 6, FR-6.12); it never builds and never judges. No builder edits them; no critic co-authors them. Enforced by `protect-floors` (FR-3.3).
- **FR-NN.8** Builders return one line. Nothing inside an artifact mentions rounds, critics, the bar or what changed. The `pair` command strips and refuses (FR-6.9, FR-15.3).
- **FR-NN.9** The assembled whole is judged and confirmed exactly as a piece: a piece of kind `whole` with the same states and transitions.
- **FR-NN.10** The paste prompt stays one block, about 230 words, 270 at most, first and last lines fixed except for the whole's noun, a user-named budget, and the second exit (FR-14.2).

### FR-1. Blindness on the filesystem

- **FR-1.1** Each role is a subagent definition under `agents/`, installed into the target repo's `.claude/agents/`, with a `tools:` allowlist: `reader` (critic): `Read, Glob, Grep, Bash`; `editor` (builder): `Read, Edit, Write, Glob, Grep, Bash`; `editor-fast` (smoother): the same tools at lower effort and a cheaper model; `author` (floor author and reference freezer): `Read, Write, Edit, Glob, Grep, Bash, WebFetch`. No role definition includes `SendMessage`, the Agent tool, the Artifact tools, graph, LSP or web search tools; those belong to the lead.
- **FR-1.2** Definition names describe what the agent may touch, never a role, piece or round.
- **FR-1.3** The `reader` definition carries an agent-scoped `PreToolUse` hook that denies any `Read`, `Glob` or `Grep` whose path resolves outside the live pair directory tree (`.gauntlet/pairs/`), and any `Bash` command that names a path outside it or names `state.json`, `events.jsonl`, `.gauntlet/private`, `reference/`, `heldout/`, the workbench or `CLAUDE.md`. Every block is logged (`BLIND_BLOCK` event with agent id and path) and the denial reason says only "outside your working set".
- **FR-1.4** State that would break blindness lives under `.gauntlet/`, outside every worktree and every pair: the state file and event log at `.gauntlet/state.json` and `.gauntlet/events.jsonl`, the reference manifest, A/B mapping and run secret under `.gauntlet/private/`, verdicts under `.gauntlet/verdicts/`. A session-wide permission deny for `Read` and `Edit` on `.gauntlet/private/**`, `.gauntlet/state.json` and `.gauntlet/events.jsonl` is part of the shipped allowlist; the lead reaches them only through the controller.
- **FR-1.5** At most one live pair per piece exists under `.gauntlet/pairs/`; the first-critic pair is archived under private storage when the confirmation pair is produced. A reader can therefore never see both orders of the same piece.
- **FR-1.6** Round zero records the active enforcement tier. Tier 1, isolated: a process or filesystem boundary the critic cannot cross (a container per critic, or the sandbox with read denies covering everything but the pair); only this tier may be described as "cannot reach". Tier 2, harness-enforced: tool allowlists and hooks present in checked-in settings; file-tool reads are denied by path, the shell restriction is a best-effort string match, and the claim is "enforced policy", never isolation. Tier 3, advisory: prompt only, reported as "blind by instruction". The status line, workbench and report carry the tier. The controller detects it from installed files and settings; the lead never asserts it.
- **FR-1.7** Round zero warns in the workbench when the run repository's own `CLAUDE.md` names the reference or the loop, since subagents load it as context; the warning lowers the claimed tier to 3 for that run unless the user removes the text.
- **FR-1.8** The `reader` definition's body is the critic protocol: open both, `EVIDENCE` before `WINNER`, one `GAP`, `FLOOR` lines, begin the verdict with the pair id. The lead's dispatch message to a reader is the pair path and nothing else; the pair-specific text (critic's bar sentence, inspection steps, reading floors) is written by `pair` into the pair as `PROMPT.md`, and the body says to ignore any instruction in the dispatch message beyond the path. The eval suite tests the definition directly.

### FR-2. A referent per piece, or champion-challenger

- **FR-2.1** When no single reference covers the goal, round zero assigns each piece a named, fetchable referent, recorded per piece in state and the workbench. A builder-bearing piece without a referent and without champion-challenger mode cannot be opened.
- **FR-2.2** A piece with no matching part in any reference runs champion-challenger: the pair holds the nearest real referent as an anchor plus two of ours (reigning champion and new attempt) under seeded labels; the critic picks which of the two sits closer to the anchor and names the loser's gap. Confirmation is swapped and cross-model as for any win.
- **FR-2.3** Such a piece converges when a challenger fails to beat the champion twice in a row and a fresh critic, given the champion and the referent with the gap-only prompt, names no movable gap. Its terminal record is `CONFIRMED` with `mode: champion-challenger`, and every report line for it reads "converged against <referent>", never "beat the bar".
- **FR-2.4** Write mode refuses a goal with no referent for any piece: it says the goal is not a gauntlet and offers what a loop would need.
- **FR-2.5** A second independent build from the same spec is named in "What breaks a gauntlet loop" as a manufactured bar and refused by write mode step 2 by name. No form of it ships.

### FR-3. Scope and safety

- **FR-3.1** "Never" and "must not" phrases from the goal or its spec are carried verbatim into the full bar sentence as invariants and into the workbench; each invariant that a command can check becomes a command floor.
- **FR-3.2** The `editor` definition carries an agent-scoped hook that denies edits to migrations, infrastructure and deploy configuration, secret and credential files, `.claude/`, `.gauntlet/`, and any path outside the piece's worktree; and denies shell commands matching deploy, publish, push, migrate and destructive patterns. Patterns are listed in the policy file. The denial message names the rule and says to return `BLOCKED: <reason>` instead of retrying.
- **FR-3.3** A settings-level hook (`protect-floors`) denies writes to `tests/required/`, `heldout/`, `reference/`, `bench/` and the eval set for every agent, the lead included, except the `author` agent during round zero and the controller's own `floor amend` command.
- **FR-3.4** A builder that returns `BLOCKED:` parks the piece with the reason under open questions; the other pieces continue. Under `/goal` this parks; it never claims a win.
- **FR-3.5** Hooks never prompt a human mid-run; they deny.
- **FR-3.6** The controller reports each hook-backed rule as enforced only when the hook is present in the target repository's checked-in or managed settings before `RUN_STARTED`; otherwise advisory. Write mode's one line under the prompt says the hooks must be checked in for enforcement.
- **FR-3.7** The status line carries `parked: n`.

### FR-4. Stalled pieces and states

- **FR-4.1** A piece is in exactly one of `ACTIVE`, `AWAITING_CONFIRMATION`, `CONFIRMED`, `INTEGRATED`, `PROMOTED`, `BLOCKED`, `PARKED`. Transitions are the table in §8.4.2 and no others.
- **FR-4.2** When the full ladder fails on the same gap, or the piece's allocation and the escalation reserve are spent, the piece parks with its last verdict and one builder account; the run continues.
- **FR-4.3** `PARKED` leaves only by a `HUMAN_RESUMED` event. The run is not ended by a parked piece.
- **FR-4.4** Held-out floors run every round before any critic and again on the merge at each wave boundary and at the gate.
- **FR-4.5** The report lists parked pieces first.

### FR-5. Honest floors and the round-zero plan

- **FR-5.1** Any test, held-out case, claim list or eval split the user did not supply is recorded as `DERIVED` in state and shown as such in the workbench.
- **FR-5.2** A defect a critic finds that a command could have caught becomes a held-out test in the same round via `gauntletctl floor add`, logged under Escalations with the old and new floor and class `evaluation`.
- **FR-5.3** A builder may return `NOT REPRODUCED: <command and output>` as its one line. The lead reruns the command through `gauntletctl rerun`, which records the observed output as a fact; when it matches the builder's, the lead records `NOT_REPRODUCED_ACCEPTED` referencing that fact, the controller marks the verdict `VERDICT_INVALID` with reason `not-reproduced`, a new critic is spawned, and the gap is not routed.
- **FR-5.4** The workbench after round zero is the plan: both bar sentences, referent per piece, the split with shared-state edges, the DERIVED floors, the invariants, the envelope. `gauntletctl commit --plan` commits it before any builder is opened.
- **FR-5.5** In an attended run the lead stops after the plan commit for approval or correction. Under `/goal` it lists the DERIVED items under open questions and proceeds on stated assumptions. The plan names what is judged and how, never how a piece is built.

### FR-6. Cost

Fewer pieces and rounds:

- **FR-6.1** Write mode and round zero ask for the coarsest split that can still be paired with a matching part of the reference and run without a shared edge. Shared state is detected from a dependency graph when one is available; schema, migration, policy and config files are shared by rule (policy file globs).
- **FR-6.2** The BUILDER prompt tells the builder to run the required suite it can already see and return only when it is green, with the output. The lead runs held-out, hostile and benchmark floors.
- **FR-6.3** Variant escalation spawns two divergent variants first; a third only if both lose.
- **FR-6.4** A builder's return is acted on in the turn it arrives (floors, pair, critic). A turn ends when the lead is waiting on subagents.

Done once:

- **FR-6.5** The reference half of every pair is prepared once per piece at round zero (`gauntletctl freeze` and `pair --prepare`): matched module extracted, names stripped, adapter attached, reference floor outputs attached. A round copies ours and assigns labels. In champion-challenger only the challenger changes.
- **FR-6.6** Floor outputs land in the pair as files: the reference's once per run, ours once per round. The critic prompt says to rerun anything it doubts.
- **FR-6.7** The confirming critic receives the same files under swapped labels; nothing is rendered again after freezing.
- **FR-6.8** The lead's own rerun of one cited command applies to wins only.

Scripted:

- **FR-6.9** `gauntletctl pair <piece>` copies ours, assigns labels from the seeded mapping, strips names and loop traces, records the mapping under private storage, opens a dispatch attempt (FR-17.12), and writes `PROMPT.md` and `PAIR_ID` into the pair from the domain template. `gauntletctl swap <piece>` produces the confirmation pair. One command per verdict.
- **FR-6.10** `gauntletctl metrics`, `status` and `gate` are computed from the event log; the lead never composes them.
- **FR-6.11** The workbench is a projection the controller regenerates on every event; the lead never edits it and, after compaction or resume, reads `gauntletctl status --full` rather than the file.

Off the lead:

- **FR-6.12** A floor author (`author` agent) writes the required suite, held-out set, hostile script and benchmark from the lead's brief, returns paths, and is discarded. The lead reviews and keeps custody.
- **FR-6.13** Reference freezing is a throwaway `author` job; the lead holds the manifest, never the bytes.
- **FR-6.14** Both are conditional on size thresholds stated in `running-the-loop.md` and the policy file (reference beyond N files, floors beyond N lines); below them the lead does the work itself.
- **FR-6.15** Builder briefs carry the matched module extract, not the reference tree.

Less loaded:

- **FR-6.16** The write-mode line under the prompt says `/effort xhigh`. Per-role effort is set in the agent definitions (`editor-fast` and `author` lower), since the harness supports it (§14.1).
- **FR-6.17** Pairs carry the matched module when the reference is large; never dependencies, build output or indexes.
- **FR-6.18** Wave smoothing runs only when pieces in the wave shared an edge, a file or one reader experience (a recorded fact). Post-smoothing rechecks run only for pieces whose diff changed something a floor cannot see.
- **FR-6.19** `example-run.md` is read on a first run or an empty workbench only.
- **FR-6.20** Write mode asks once for a budget alongside the bar pick, carries it into the first line when given, and declines to write a prompt for work too small for a loop (a single piece with no measurable half and no taste dimension).

### FR-6b. Less loaded per session

- **FR-6b.1** The `SKILL.md` frontmatter description is two lines: what it does, and the trigger words.
- **FR-6b.2** `SKILL.md` holds write mode only, target 6 KB, hard ceiling 7 KB. Run mode, the Portability detail and the "What breaks" rationale move to `references/`.
- **FR-6b.3** `running-the-loop.md` keeps rules, dispatch prompts and templates, drops the argument for each rule, and stays under 10 KB.
- **FR-6b.4** Run mode reads `running-the-loop.md`, one domain file and the harness file by default; `controller.md` and `example-run.md` only on the conditions stated.

### FR-7. Harness quarantine

- **FR-7.1** Every Claude Code specific (`/goal`, `/loop`, `ultracode`, `wt`, `SendMessage`, the subagent cap variable, hook rules, per-agent model and effort, sandbox and permission keys) lives in one dated `references/harness-claude-code.md`. Method files reference it and contain no harness commands.
- **FR-7.2** The harness file says what to do when each command is unavailable, and carries the install steps for agents, hooks, allowlist and controller into a target repository.
- **FR-7.3** The controller is harness-agnostic: it reads and writes files and runs shell commands the lead names; it never calls a harness API.

### FR-8. Write mode

- **FR-8.1** Flow step 2 tests a user-supplied bar and refuses, by name, a manufactured bar (a second build from the same spec) and a suite alone, offering per-piece referents instead.
- **FR-8.2** The paste prompt's first line carries the different-model rule and the second exit.
- **FR-8.3** A third filled example covers a bespoke internal system: per-piece referents, one champion-challenger piece, a human-gate line, a budget clause. All three examples stay under 270 words.

### FR-9. Attribution

- **FR-9.1** The README credits robonuggets/gauntlet-loop (write-mode skeleton, bar tests, worked examples) and trilwu/gauntlet-loop-skills (run-mode structure, domain files) alongside Shumer, and states which of their decisions this skill reversed. See §16, C1.

### FR-10. Loose ends

- **FR-10.1** `design.md`'s pair preparation renders ours only; the reference render is reused frozen.
- **FR-10.2** The "Deck, doc, deliverable" row leaves the bar table (default; see C6).
- **FR-10.3** The whole-gate turn ends with the pasted output of `gauntletctl gate`, listing the two whole-gate verdict files and their WINNER lines.

### FR-11. The skill is tested

- **FR-11.1** `eval/write-mode/` holds at least twelve goals, including two with no fetchable bar, one too small for a loop, one with a manufactured bar, one carrying a "never" invariant, and the manufactured-bar run that motivated the intent. Each case states its expected checks: a fetchable bar named; the exit line carries the different-model rule; a budget clause appears only when named; bad bars refused; invariants reach the prompt; prompt under 270 words.
- **FR-11.2** `eval/critic/` holds, per domain, at least three frozen pairs (known-good against known-bad, twice; one near-tie), run through the critic prompt in both orders. Pass: the known-better side wins in both orders; the near-tie yields a WINNER line and no hedge.
- **FR-11.3** The suite runs non-interactively (`claude -p` with a restricted tool list and a check script), on every change to `SKILL.md`, `references/`, `hooks/`, `agents/`, `policy/` or `eval/`, and a pass rate below the recorded baseline blocks the merge.
- **FR-11.4** Every run that exposes a gap in the skill becomes a permanent case.

### FR-12. Pipeline fit

- **FR-12.1** Write mode accepts a `spec.md` or `intent.md` path as the goal. "Never" and constraint sentences become invariants (up to three verbatim in the prompt, all in the workbench); acceptance criteria become DERIVED floors until the user confirms them.
- **FR-12.2** `gauntletctl commit` commits the run's artifacts with the diff after a secret scan: reference manifest, both bar sentences, the round-zero workbench, the final workbench, every verdict file, the event log, the report. It never commits `.gauntlet/private/`, `pairs/`, or the reference bytes.
- **FR-12.3** The lead opens a PR (`gauntletctl promote` wraps `gh pr create`) whose description links the manifest, workbench and whole-gate verdicts. No run merges its own result; `PROMOTED` requires a `PR_MERGED` event recorded from the remote, not from the lead.
- **FR-12.4** The PR's compliance pass checks the diff against the full bar sentence and the two whole-gate verdicts.
- **FR-12.5** A whole-gate loss whose gap traces to the goal rather than the build is filed as class `scope` and written as an intent draft under the report, never as a coherence piece.

### FR-13. Self-measurement

- **FR-13.1** `gauntletctl metrics` computes from the event log: rounds per confirmed piece; red-floor share of rounds; confirmation flip rate; discarded-verdict rate; accepted `NOT REPRODUCED` rate; parked pieces; escalations per piece by trigger (repeated gap or spent allocation); invocations per confirmed piece; local, escalation and whole-gate spend against allocation; unused reserve; ceiling-hit rate; plus every value-column metric in the mechanism table (FR-M.3).
- **FR-13.2** The report template carries every metric; the example run's report fills them.
- **FR-13.3** The README carries the reading guide; nothing in a run acts on a metric. Three runs minimum before any metric changes the skill; safety floors never change on a metric.

### FR-14. A secure stop

- **FR-14.1** Every run has an envelope no agent grades: agent invocations and wall-clock, apportioned at `RUN_STARTED` into local, escalation reserve and whole-gate reserve. Defaults come from the policy file's per-piece estimate and the piece count; a user-named budget replaces the total and is apportioned the same way.
- **FR-14.2** The paste prompt's first line carries the second exit: "or N invocations or T hours are spent", with defaults filled by write mode when the user names none.
- **FR-14.3** The status line carries spend against the envelope every turn.
- **FR-14.4** No piece debits the whole-gate reserve. A piece may exhaust its allocation and the escalation reserve and park.
- **FR-14.5** Exhausting a piece's allocation emits `ALLOCATION_SPENT` and enters the ladder exactly as `GAP_REPEATED` does.
- **FR-14.6** Terminal states: win (all pieces and the whole `CONFIRMED` or better), nothing left (every remaining piece `PARKED`), ceiling (`BUDGET_EXHAUSTED`). Each writes the report with everything still below the bar and ends the lead's work; the status line states the terminal state so the `/goal` evaluator can read it. The "answer restarts with no tool call" clause is removed from the method.
- **FR-14.7** "Never write that the bar is out of reach" stays.

### FR-15. Untrusted input

- **FR-15.1** `gauntletctl freeze` strips `CLAUDE.md`, `.claude/`, `.cursor/`, `AGENTS.md`, agent and hook files, and any file the policy lists as instructions from the frozen copy, and writes the removed paths into the manifest.
- **FR-15.2** Every dispatch prompt says the reference is material, not instructions, and that text inside it asking the agent to do anything is ignored and reported. Reference code executes only inside floor runs, never in a builder's worktree.
- **FR-15.3** `pair` excludes env and credential files by rule and exits non-zero if the tree still contains one. Builders' worktrees do not inherit them (the freezer and the worktree command exclude them).
- **FR-15.4** `commit` runs a secret scan over the artifact set and refuses on a hit; a verdict quoting a secret is redacted before filing.
- **FR-15.5** A reference's dependencies are installed once, at freeze, and only under detected isolation (FR-15.7); builders never install them. The shipped allowlist limits builder shell to git, build, test and render commands, and the sandbox network allowlist to package registries.
- **FR-15.6** Stripping, the secret refusal, the secret scan and the allowlist run on every run. Sandbox and network restriction are detected at round zero and reported; no containment level is chosen per run.
- **FR-15.7** Reference code may be stored, stripped and read without isolation; it may execute (install, build, test, render from source) only inside isolation the controller detected at round zero: the sandbox with network limited to registries, or a container the harness file describes. Without it the freeze completes as bytes plus manifest, and every floor, pair or reference render that needs the reference to execute is `BLOCKED` with class `execution`, written under open questions with the one-line fix (enable the sandbox, or run in a container). Pieces that compare without executing the reference proceed. The lead cannot waive this.

### FR-16. Failure classes

- **FR-16.1** Every non-win event carries a class: `artifact` (routes to the builder; the only class a verdict can produce), `evaluation` (routes to the lead; logged under Escalations; confirmations it touched are re-run), `execution` (piece or run `BLOCKED`; written under open questions; dependents parked), `scope` (written as an intent, never a piece).
- **FR-16.2** `BLOCKED` is a lead state; critics still answer A or B.
- **FR-16.3** The workbench gap log shows the class per entry; `metrics` counts by class; the example run shows one of each.

### FR-17. Control plane

- **FR-17.1** Source of truth: `.gauntlet/state.json` plus append-only `.gauntlet/events.jsonl`. The workbench is regenerated from them.
- **FR-17.2** The state machine of §8.4.2 is enforced in code; illegal transitions are rejected with a non-zero exit and a message.
- **FR-17.3** The lead records judgment events with `gauntletctl event <name> [fields]` and nothing else; fact events are produced only by controller commands that observed the fact (§8.4.6), and `event` rejects a fact event name. It never edits state. A settings-level hook denies writes to the state file, the event log, private storage, and the controller's own files from every agent's tools, and denies `gauntletctl attest` from any tool call; the controller process is the only writer.
- **FR-17.4** `gauntletctl next` prints the legal actions for the current state. Mechanical actions (prepare pair, run floors, emit critic prompt, swap, regenerate workbench, status) it performs itself when asked; judgment actions (where to split, which module pairs, which referent, variant approaches) it names for the lead, with the event the lead must record afterwards.
- **FR-17.5** The policy file is versioned; `RUN_STARTED` records the version; the controller refuses a version change mid-run. The policy has no parameter for critic count, critic strength, confirmation, blindness or the definition of a win.
- **FR-17.6** Budgets are escrow the controller debits per event; the whole-gate reserve has no debit path from any piece.
- **FR-17.7** `ACTIVE` and `AWAITING_CONFIRMATION` pieces carry owner, attempt id and lease expiry; `LEASE_EXPIRED` moves the piece to `BLOCKED`.
- **FR-17.8** `pair` and `swap` are idempotent per run, piece and round: the label mapping is derived from an HMAC of the run secret over run id, piece and round; a retry reproduces the same files and mapping.
- **FR-17.9** Authorities are fixed: model judges; controller transitions and accounts; scripts establish facts; humans handle exceptions (new bar as a new run, scope change, resume, PR approval, policy version).
- **FR-17.10** A run that finds itself wanting a helper script marks the piece `BLOCKED` and parks it; it never writes tooling. The controller ships with tests.
- **FR-17.11** One lead model; no meta-agents.
- **FR-17.12** Verdict provenance. Every critic dispatch creates an immutable attempt record: run, piece, round, pair id, attempt id, expected agent type, expected model. A verdict is accepted only when the harness's subagent-stop hook delivered it to the controller from an agent of the expected type, it names the open attempt's pair id, and its observed model matches the attempt (and differs from the first critic's for a confirmation). `CRITIC_WIN`, `CRITIC_LOSS`, `CONFIRMATION_WIN`, `CONFIRMATION_LOSS` and `VERDICT_INVALID` are derived by the controller from the attested verdict and the mapping; the lead cannot submit them. The same path attests `BUILDER_DONE` from `editor` agents. The lead may route a critic; it cannot manufacture its result.

### FR-M. The mechanism table

- **FR-M.1** The README carries the mechanism table from the intent with all five columns.
- **FR-M.2** `running-the-loop.md` states each row's bound and exit where the mechanism is described.
- **FR-M.3** `gauntletctl metrics` emits every metric named in the value column.
- **FR-M.4** A new mechanism enters the skill only with all five columns filled; a human removes a mechanism whose value column stays empty across three measured runs.

## 6. Non-functional requirements

| Area | Requirement |
| --- | --- |
| Size | `SKILL.md` ≤ 7,000 bytes (target ~6,000). Frontmatter description ≤ 2 lines. `running-the-loop.md` < 10,240 bytes. `controller.md` one page (≤ 6,000 bytes). Write mode's default loaded text (`SKILL.md` plus one domain file) under half of the baseline's 16,030 + ~3,700 bytes. Prompt ≤ 270 words. |
| Cost | No new fixed per-critic overhead. Reference preparation and reference floors once per run. The README's cost estimate is replaced by measured numbers after three runs. |
| Determinism | State transitions are a deterministic function of the current state, the event and the pinned policy. Commands with external effects (`freeze`, `floors`, `rerun`, `scan`, `commit`, `promote`, `status` against the remote, `attest`) execute the effect and record what they observed as a fact event, so replaying the event log reproduces the state exactly. `pair`/`swap` are idempotent on retry. |
| Security | §11. Blindness and boundary rules enforced at Tier 2 when settings are checked in; every claim states the detected tier, and Tier 2 is never described as isolation. Reference code executes only under detected isolation (FR-15.7). Fact events enter only through the controller's own observation (FR-17.12). |
| Portability | Method files contain no harness tokens outside the Portability section and the harness file. Controller runs anywhere its runtime runs. |
| Testability | Controller tests cover every illegal transition and every subcommand's idempotence. Eval suite green on the release commit and wired to the paths in FR-11.3. |
| Observability | Event log is the audit trail; metrics computed from it only; status line every turn. |
| Maintainability | One README entry per changed decision in the existing shape (alternative, why, cost, evidence); rule ledger marks each rule advisory or enforced. |
| Compatibility | The paste prompt of the baseline still runs: a prompt without the second exit or the different-model rule is accepted and the lead applies policy defaults. |

## 7. Business rules

### 7.1 Non-negotiables

The ten rules of the intent's "what must not change" section, verbatim, are rules of this specification (FR-NN.1 through FR-NN.10). No requirement below weakens one; any change set touching one shows it still holds.

### 7.2 The refusal

The strength of a check never varies at run time. No rigor level per run or per piece; no win "clear enough" to skip confirmation; no early round with weaker verification. Adaptivity lives in what gets built and how work is routed. The only route to changing check strength is cross-run evidence read by a human changing the README for the next release.

### 7.3 Authorities

| Authority | May | May not |
| --- | --- | --- |
| Model (lead) | Judge: split, referent, mode, variant approaches, same-gap calls, park and block requests; dispatch subagents; route gaps | Submit a fact event; edit state; change policy; end the run; merge |
| Controller | Transition, account, prepare pairs, run floors, write pair prompts, attest subagent results, translate verdicts through the mapping, regenerate the workbench, compute metrics | Make a judgment call; change what a win is |
| Script | Establish a fact: pass or fail, a number | Grade |
| Human | Change the bar (new run), change scope, resume a parked piece, approve the PR, change the policy version | Be asked mid-run by a hook |

### 7.4 Enforced versus advisory

A rule is **enforced** when a hook, tool limit, controller check or branch protection stands behind it and the mechanism was present before `RUN_STARTED`. Otherwise it is **advisory**. The README ledger, the round-zero record and the report state which applied.

## 8. Proposed design

### 8.1 Package layout

```
gauntlet-loop/
  SKILL.md                         write mode only
  README.md                        decisions D1-D15 + new entries, rule ledger, mechanism table, metrics guide, attribution
  references/
    running-the-loop.md            run mode: rules, dispatch prompts, workbench and report templates
    controller.md                  states, events, transitions, artifacts per transition, budgets, escalation, authorities
    harness-claude-code.md         dated; every harness fact, command, fallback and install step
    what-breaks.md                 the "What breaks a gauntlet loop" rationale and the Portability detail
    example-run.md                 one run retold as an event log with status lines
    domains/*.md                   coding, design, writing, research, data-analysis, detection, prompt-eval
  bin/gauntletctl                  the controller, one executable
  policy/v1.json                   pinned policy (see 8.4.5)
  hooks/                           critic-blind, builder-boundary, protect-floors, controller-only
  agents/                          reader.md, editor.md, editor-fast.md, author.md
  permissions/allowlist.json       minimal allow and deny rules for a run
  eval/                            write-mode cases, critic pairs, check script, runner, baseline
  tests/                           controller tests
```

Run-time layout in a target repository, created by `gauntletctl init`:

```
.gauntlet/
  events.jsonl                     append-only; committed at the end
  workbench.md                     projection; committed at plan and at the end
  verdicts/<piece>-r<n>-<1|2>.md   committed
  report.md                        committed
  pairs/<piece>/                   one live pair per piece; never committed
  state.json                       source of truth; never committed; tool reads denied (controller only)
  private/                         secret, mapping/, archived pairs, manifest; never committed; tool reads denied
reference/                         frozen copy; manifest committed, bytes not
tests/required/  heldout/  bench/  lead-owned floors
```

### 8.2 Write mode flow

1. Read the goal, or the spec/intent file it names (FR-12.1). Extract invariants and candidate floors.
2. Set the bar: test a supplied bar against named, fetchable, comparable, and against the two refusals (manufactured bar, suite alone). Offer replacements or candidates. Ask once for a budget. Wait for the pick. Refuse work too small for a loop and goals with no referent for any piece.
3. Write the prompt: one block; first line with the different-model rule and the second exit (defaults from policy when unnamed); invariants inside the bar sentence.
4. One line under it: paste as is, `/effort xhigh`, auto mode or the shipped allowlist, hooks checked in for enforcement.

### 8.3 Run mode flow

1. **Round zero.** Read `running-the-loop.md`, the domain file, the harness file. `gauntletctl init` (run id, secret, policy version, tier detection, containment detection, CLAUDE.md warning). Freeze (via `author` when over threshold), strip, manifest. Bar sentences. Split coarse-first with referent per piece; champion-challenger mode where no referent part exists. Floors (via `author` when over threshold), marked DERIVED where the user supplied none. Envelope apportioned. `pair --prepare` per piece. `commit --plan`. Attended: stop for approval. Open pieces.
2. **A round.** The builder returns one line; the `SubagentStop` hook attests it and the controller records `BUILDER_DONE`. `floors <piece>` runs held-out, hostile and benchmark (the builder already ran required) and records `FLOOR_PASS` or `FLOOR_FAIL`. Red: gap routed, round over. Green: `pair <piece>` copies ours, assigns labels, writes `PROMPT.md`, opens the attempt; the lead spawns a `reader` with the pair path; the hook attests the verdict and the controller records `CRITIC_RESULT`, checks shape and citations, and translates `WINNER` through the mapping into `CRITIC_WIN`, `CRITIC_LOSS` or `VERDICT_INVALID`. Loss: the lead routes the gap. Win: `swap <piece>`; the lead spawns a `reader` on a different model; the same path yields `CONFIRMATION_WIN` or `CONFIRMATION_LOSS`. `next` after every event.
3. **Escalation.** `GAP_REPEATED` or `ALLOCATION_SPENT` advances the ladder; the controller names the rung; the lead performs the judgment part and records it.
4. **Wave boundary.** `WAVE_COMPLETE`; smoother (`editor-fast`) only if a shared edge is recorded; floors; recheck only judgment-visible diffs; `INTEGRATED`.
5. **Gate.** The `whole` piece: smooth, floors, pair, critic, confirm. `gate` prints the two verdict files and WINNER lines. A loss opens a coherence piece or files a scope failure.
6. **End.** `commit`, `promote` (PR), report. `PROMOTED` on `PR_MERGED` from the remote.

### 8.4 The controller

#### 8.4.1 Subcommands

| Command | Kind | Does |
| --- | --- | --- |
| `init` | mechanical | Creates `.gauntlet/`, run id, secret (0600), pins policy version, detects tier and containment, writes `RUN_STARTED` |
| `freeze <src> <dst>` | mechanical | Copies or clones, strips instruction files and credentials, installs dependencies once, writes manifest and `REFERENCE_FROZEN` |
| `piece open|split|referent|mode` | judgment recorded | Opens pieces with parent, referent, mode, allocation; `PIECE_OPENED` |
| `floor add|amend|list` | mechanical | Registers floors with `DERIVED` flag and command; `amend` logs old and new |
| `floors <piece>` | mechanical | Runs lead-side floors on ours; writes outputs; `FLOOR_PASS` or `FLOOR_FAIL` |
| `pair <piece> [--prepare]` | mechanical | Reference half once; ours per round; labels from seed; strip; refuse on secrets; emit prompt |
| `swap <piece>` | mechanical | Confirmation pair, order inverted, same files |
| `event <name> [k=v...]` | judgment record | Accepts judgment events only (§8.4.6); validates required fields and referenced facts; applies the transition or rejects |
| `attest` | fact, hook-invoked | Reads the `SubagentStop` payload on stdin; records `BUILDER_DONE`, `CRITIC_RESULT`, `SMOOTHER_DONE` or `FLOORS_AUTHORED` bound to agent id, agent type, attempt and observed model; derives win, loss or invalid from the verdict and the mapping |
| `next` | mechanical | Legal actions now; which are mechanical, which need the lead |
| `rerun <piece> <cmd>` | fact | Re-executes a cited command for `NOT REPRODUCED` and the win-side rerun |
| `status [--full]` | mechanical | The status line verbatim; `--full` is the resume view |
| `workbench` | mechanical | Regenerates the projection |
| `metrics` | mechanical | The FR-13.1 numbers |
| `gate` | mechanical | Whole-gate evidence: two verdict paths and their WINNER lines |
| `scan` | fact | Secret scan of the artifact set |
| `commit [--plan]` | mechanical | Scan, stage the committed set, commit |
| `promote` | mechanical | Opens the PR; records `PR_OPENED`; `PR_MERGED` is read from the remote on a later `status` |
| `resume <piece>` | human | Records `HUMAN_RESUMED`; documented as human-only, logged with actor |

#### 8.4.2 State machine

| From | Event | To | Required artifacts |
| --- | --- | --- | --- |
| (none) | `PIECE_OPENED` | `ACTIVE` | referent or mode; allocation; `REFERENCE_FROZEN` exists |
| `ACTIVE` | `BUILDER_DONE` | `ACTIVE` | artifact path |
| `ACTIVE` | `FLOOR_PASS` / `FLOOR_FAIL` | `ACTIVE` | floor outputs file |
| `ACTIVE` | `CRITIC_LOSS` / `VERDICT_INVALID` | `ACTIVE` | verdict file; class |
| `ACTIVE` | `CRITIC_WIN` | `AWAITING_CONFIRMATION` | `FLOOR_PASS` this round; verdict file; pair id |
| `AWAITING_CONFIRMATION` | `CONFIRMATION_WIN` | `CONFIRMED` | swapped pair id; model id differs from first; verdict file |
| `AWAITING_CONFIRMATION` | `CONFIRMATION_LOSS` | `ACTIVE` | verdict file; gap |
| `ACTIVE` | `GAP_REPEATED` / `ALLOCATION_SPENT` | `ACTIVE` | ladder rung advanced |
| `CONFIRMED` | `WAVE_COMPLETE` (+ floors green, recheck if any) | `INTEGRATED` | merge commit; floor outputs |
| `INTEGRATED` | `RECHECK_LOSS` | `ACTIVE` | verdict file |
| `INTEGRATED` | `PR_MERGED` | `PROMOTED` | remote merge evidence |
| `ACTIVE` / `AWAITING_CONFIRMATION` | `PIECE_BLOCKED` / `LEASE_EXPIRED` | `BLOCKED` | reason; class `execution` |
| `BLOCKED` | `BLOCKER_CLEARED` | `ACTIVE` | note |
| `ACTIVE` / `BLOCKED` | `PIECE_PARKED` | `PARKED` | last verdict; builder account |
| `PARKED` | `HUMAN_RESUMED` | `ACTIVE` | actor |

Rejected explicitly: `ACTIVE → PROMOTED`, `PARKED → PROMOTED`, `→ CONFIRMED` without `CONFIRMATION_WIN`, `CONFIRMED → PROMOTED` without `INTEGRATED`, any exit from `PARKED` other than `HUMAN_RESUMED`, `PIECE_OPENED` before `REFERENCE_FROZEN`, and any fact event submitted through `event`. Run-level and provenance events: `RUN_STARTED`, `REFERENCE_FROZEN`, `PLAN_COMMITTED`, `CRITIC_DISPATCHED`, `CRITIC_RESULT`, `WHOLE_GATE_WIN`, `WHOLE_GATE_LOSS`, `BUDGET_EXHAUSTED`, `RUN_ENDED(reason)`, `BLIND_BLOCK`, `BOUNDARY_BLOCK`. The `whole` piece uses the piece machine. Every event is fact or judgment per §8.4.6.

#### 8.4.3 Budgets

Envelope `E` in invocations and `T` in hours. Accounts: local `L`, escalation reserve `R`, whole-gate reserve `G`, proportions from policy. Per-piece allocation `a = L / pieces` at open; a split gives each child the parent's remainder split evenly. Debits: one per subagent spawn, recorded with the event that caused it. `a` reaching zero emits `ALLOCATION_SPENT`; ladder rungs beyond the piece's allocation debit `R`; `R` at zero with the ladder unfinished parks the piece. `G` is debited only by the `whole` piece. `E` or `T` reached emits `BUDGET_EXHAUSTED` and ends the run with a report.

#### 8.4.4 Leases and idempotence

Lease: owner (agent id), attempt id, expiry (policy default, hours). `status` checks expiries and emits `LEASE_EXPIRED`. Mapping seed: `HMAC-SHA256(secret, run_id|piece|round)`; label A is ours when the first bit is 1; `swap` inverts; the mapping file lives under private storage.

#### 8.4.5 Policy `v1.json`

Fields: `version`; envelope proportions and per-piece estimate; wall-clock default per piece; lease hours; ladder order and variant counts (2 then 1); shared-by-rule globs; builder boundary path and command patterns; instruction-file strip list; credential file globs; offload thresholds (reference files, floor lines); secret-scan patterns. Absent by design: anything about critic count, strength, confirmation, blindness, win.

#### 8.4.6 Event classes and provenance

**Judgment events**, the only names `event` accepts from the lead, each with the lead as actor: `SPLIT_DECIDED`, `REFERENT_SELECTED`, `MODE_SELECTED`, `VARIANT_APPROACHES_SELECTED`, `GAP_SAME_AS_LAST`, `GAP_ROUTED`, `NOT_REPRODUCED_ACCEPTED` (must reference a `RERUN_OBSERVED` fact), `PARK_REQUESTED` (reason, class), `BLOCK_REQUESTED` (reason), `SHARED_EDGE_RECORDED`, `SCOPE_FAILURE_FILED`.

**Fact events**, produced only by the controller from something it observed or derived: `RUN_STARTED`; `REFERENCE_FROZEN` (`freeze`); `FLOOR_PASS`, `FLOOR_FAIL` (`floors`); `CRITIC_DISPATCHED` (`pair`, `swap`); `BUILDER_DONE`, `CRITIC_RESULT`, `SMOOTHER_DONE`, `FLOORS_AUTHORED` (`attest`, from the harness's `SubagentStop` hook); `CRITIC_WIN`, `CRITIC_LOSS`, `CONFIRMATION_WIN`, `CONFIRMATION_LOSS`, `VERDICT_INVALID` (derived from `CRITIC_RESULT` and the mapping); `GAP_REPEATED` (derived from `GAP_SAME_AS_LAST`); `ALLOCATION_SPENT`, `BUDGET_EXHAUSTED` (accounting); `LEASE_EXPIRED` (`status`); `RERUN_OBSERVED` (`rerun`); `SCAN_PASSED`, `SCAN_FAILED` (`scan`); `PLAN_COMMITTED`, `ARTIFACTS_COMMITTED` (`commit`); `PR_OPENED` (`promote`); `PR_MERGED` (`status` against the remote); `BLIND_BLOCK`, `BOUNDARY_BLOCK` (hooks); `PIECE_PARKED`, `PIECE_BLOCKED` (derived from a request, the ladder or accounting); `PIECE_OPENED`, `WAVE_COMPLETE`; `HUMAN_RESUMED` (`resume`, actor human).

**Provenance.** `pair` and `swap` open a dispatch attempt: run id, piece, round, pair id, attempt id, expected agent type, expected model, opened-at. The `SubagentStop` hook, matched on the role definitions, pipes its payload (`agent_id`, `agent_type`, `last_assistant_message`, `transcript_path`) to `attest`. `attest` accepts a verdict only when the agent type is `reader`, the verdict's first line names an open attempt's pair id, the pair is still live, the observed model (C11) equals the attempt's expected model and, for a confirmation, differs from the first critic's, and the verdict has the shape with at least one citation. Otherwise it records `CRITIC_RESULT` with `valid: false` and the reason, which becomes `VERDICT_INVALID`. `CONFIRMED` therefore means a qualifying reader execution produced the result, not that the lead reported one. The guarantee is as strong as the run's tier: at Tier 2 a lead could still reach `attest` through an unmatched shell form, and the ledger says so.

### 8.5 Enforcement

| Hook | Where | Event and matcher | Denies | For whom |
| --- | --- | --- | --- | --- |
| `critic-blind` | `agents/reader.md` frontmatter | `PreToolUse` on `Read|Glob|Grep|Bash` | paths outside `.gauntlet/pairs/`; commands naming private state, reference, held-out, workbench, `CLAUDE.md` | readers only |
| `builder-boundary` | `agents/editor.md`, `editor-fast.md` frontmatter | `PreToolUse` on `Edit|Write|Bash` | policy path and command patterns; anything outside the worktree | builders and smoother |
| `protect-floors` | target repo `.claude/settings.json` | `PreToolUse` on `Edit|Write|Bash` | writes to `tests/required/`, `heldout/`, `reference/`, `bench/`, eval set, unless `agent_type` is `author` during round zero or the command is `gauntletctl floor` | every agent and the lead |
| `controller-only` | target repo `.claude/settings.json` | `PreToolUse` on `Edit|Write|Bash` | writes to `.gauntlet/private/`, `events.jsonl`, `state.json`, `bin/gauntletctl`, `policy/`, `hooks/`, `agents/`; `git add|commit` touching `.gauntlet/` unless via `gauntletctl commit`; any tool invocation of `gauntletctl attest` | every agent and the lead |
| `attest` | target repo `.claude/settings.json` | `SubagentStop`, matcher `reader|editor|editor-fast|author` | nothing; pipes the payload to `gauntletctl attest`, which records the fact | every role |

Each denial returns `permissionDecision: deny` with a reason that names the rule and the expected next step. Hooks in the target repo's settings fire inside subagents and carry `agent_id` and `agent_type`; `SubagentStop` also carries the agent's last message (verified, §14.1). The Bash checks are string matches, so Tier 2 is reported as enforced policy, never as isolation.

Agent definitions: `tools:` as in FR-1.1; no `SendMessage` in any role (so the sibling roster is never shown); the `reader` body is the critic protocol (FR-1.8); `model:` unset for `reader` and `editor` (the lead passes it per call) unless C11 pins two reader definitions, `sonnet`-class for `editor-fast`; `effort:` unset for `reader` and `editor` (inherit the session's `xhigh`), `high` for `editor-fast` and `author`; no `memory:`; no `skills:`.

Allowlist (`permissions/allowlist.json`): allow `git`, the domain's build, test and render commands, `gauntletctl`; deny `Read`/`Edit` on `.gauntlet/private/**`, `.gauntlet/state.json`, `.gauntlet/events.jsonl`, secrets and env files; `permissions.blockReadsOutsideWorkingDirectories: true`; a recommended sandbox block with `network.allowedDomains` limited to registries and `credentials` deny entries. The controller must run outside sandbox read denies that cover private storage (§16, C5).

### 8.6 What moves where

| Baseline text | Destination |
| --- | --- |
| `SKILL.md` § Run mode, § Portability detail, § What breaks | `references/running-the-loop.md`, `harness-claude-code.md`, `what-breaks.md` |
| `running-the-loop.md` "Why each rule is there" table and per-rule arguments | `README.md` |
| `running-the-loop.md` § What the harness must have | `harness-claude-code.md` |
| Workbench template | stays, as the projection's shape; new columns: state, class, referent, mode, allocation spent, tier |
| Report | stays; new fields: parked first, tier, containment, metrics, envelope |
| `example-run.md` | retold as events with `next` outputs and status lines; adds one of each failure class, one champion-challenger piece, a DERIVED floor, a finding converted to a floor, round-zero commit, PR at the end |

### 8.7 Eval suite

`eval/run.sh` runs each write-mode case through `claude -p` with the skill loaded and tools restricted, captures the prompt, and `eval/check.py` applies the case's checks. Critic cases spawn a `reader` on the frozen pair in both orders and check the WINNER lines. `eval/baseline.json` records the pass rate; CI fails below it. The workflow file lives in the repository root (`.github/workflows/gauntlet-eval.yml`) with path filters from FR-11.3 (§16, C4).

### 8.8 The minimal path

The cheapest complete run, and the only thing that runs unconditionally:

```
valid reference (fetched, frozen, stripped)
  → round zero (bar sentences, coarse split, floors, envelope, plan commit)
  → builder runs the required floor itself and returns one line
  → lead-side floors (held-out, hostile, benchmark)
  → blind A/B, one fresh reader
      loss → gap routed, repeat
      win  → swapped confirmation on a different model
  → piece confirmed
  → whole gate (floors; A/B; confirmation)
  → commit, PR
```

Everything else runs only when its trigger fired, and every trigger is a recorded fact: `GAP_REPEATED` or `ALLOCATION_SPENT` for the ladder; `SHARED_EDGE_RECORDED` for wave smoothing and the gate smoother; a judgment-visible diff for a recheck; a piece with no pairable referent for champion-challenger; the size thresholds for the floor author and the freezer; an empty workbench for `example-run.md`; a whole-gate loss for a coherence piece. Nothing expensive runs because the mechanism exists.

## 9. Architecture and boundaries

- **Dependency direction.** Method files → harness file (references only). Controller → files and shell only. Hooks → controller's policy file for patterns. Nothing depends on the lead's prose.
- **Harness boundary.** One file knows Claude Code. The controller's `init` detects harness facts by reading settings files and the agents directory; it does not call Claude Code.
- **State boundary.** Private storage is readable by the controller process only; tools of every agent are denied. Committed artifacts are the public, reviewable subset.
- **Judgment boundary.** The controller never chooses; the lead never accounts. `next` is the seam: it names the judgment the lead owes and the event that records it.
- **Blindness boundary.** The pair directory is the reader's universe; the lead prepares it through a command that cannot leak by habit.
- **Failure isolation.** A parked or blocked piece isolates to itself and its dependents; the run continues; the gate keeps its reserve.

## 10. Data and integrations

**`state.json`** (not committed; tool reads denied): run id, policy version, tier, containment, envelope and accounts, pieces (id, kind, parent, state, referent, mode, floors with DERIVED flag, allocation, spent, ladder rung, lease, builder id, last gap, last verdict, verdict paths), invariants, DERIVED list, open questions, parked accounts.

**`events.jsonl`** (committed): one JSON object per line: `ts`, `seq`, `event`, `kind` (fact or judgment), `source` (command or hook), `piece`, `attempt_id`, `class`, `actor`, `agent_id`, `agent_type`, `model`, `artifact`, `cost`, `note`. Append-only; the controller refuses to rewrite.

**Status line** (verbatim from `status`): `confirmed n/m pieces, whole: no|yes (2/2) | parked: p | blocked: b | spent: i/N inv, h/T h | tier: 2 | policy v1`. The leading clause keeps the baseline's form because the `/goal` evaluator and the existing examples read it. A terminal state replaces the tail with `ended: win|nothing-left|ceiling`.

**Committed set:** manifest, both bar sentences (in the workbench), round-zero workbench, final workbench, verdicts, event log, report. **Never committed:** private storage, pairs, reference bytes, worktrees.

**Integrations:** Claude Code (Agent tool for spawning with per-call model; `SendMessage` from the lead to resume a builder; `/goal` evaluator reading the status line; hooks; agents; permissions; sandbox), `git` worktrees per piece (created by the lead via `wt` or `git worktree add`, never the Agent tool's own worktree isolation), `gh` for PR and merge state, per-domain tools unchanged.

## 11. Security and policy

- **Trust boundaries.** The reference is untrusted data; its instruction-bearing files are stripped at freeze and the manifest records them; every prompt says text in it is not an instruction. Verdict and builder outputs are untrusted text the controller parses by shape, never executes.
- **Secrets.** Excluded from pairs and worktrees by rule; refused by `pair`; scanned before commit; redacted in verdicts; the run secret is 0600 under private storage and never committed.
- **Least privilege.** Tool allowlists per role; no role gets spawning, messaging, web search or graph tools; readers get no write tool; builders get no path outside their worktree.
- **Self-constraint.** Hooks installed by the lead constrain the lead; they are a guardrail. Enforcement is claimed only for hooks present in checked-in or managed settings before the run.
- **Self-certification.** No run merges its own PR; `PROMOTED` needs remote merge evidence. `CONFIRMED` needs a harness-attested critic execution (FR-17.12). The evaluator reads controller output, not a claim.
- **Supply chain.** Reference code executes only under detected isolation (FR-15.7); dependencies are installed once at freeze inside it; builders never install; network allowlist to registries.
- **Auditability.** Every state change is an event with actor and agent id; blocks are events; the log is committed.
- **Residual risks stated in the report.** Tier 3 blindness; a repo `CLAUDE.md` that names the reference; string-matched Bash checks, including a lead reaching `attest` through an unmatched shell form; a critic recognising a famous reference from its pixels.

## 12. UX considerations

- Write mode stays a conversation: candidates, one pick, one budget question, one prompt, one line under it.
- Refusals name the test that failed and offer the nearest thing that passes.
- The workbench reads as a complete report at any moment, parked pieces first, with the tier and containment stated.
- Hook denials tell the agent what to return instead, so a block becomes a parked piece rather than a retry loop.
- The lead's turn ends on the controller's status line, unchanged in its first clause from what users and examples already know.

## 13. Acceptance criteria

- **AC-NN.1** Controller test: `PIECE_OPENED` before `REFERENCE_FROZEN` is rejected. **AC-NN.5** `CONFIRMATION_WIN` with the same model id as the first critic is rejected. **AC-NN.10** Each of the three examples and the template count ≤ 270 words.
- **AC-1.1** From a spawned `reader`, listing readable paths and tools yields nothing naming the reference, mapping, loop or builder. **AC-1.2** A reader's attempt to read the workbench is denied and a `BLIND_BLOCK` event is logged. **AC-1.3** A run with no hooks installed reports Tier 3 in status, workbench and report; a Tier 2 report never uses the words "isolated" or "cannot reach". **AC-1.4** README "why each rule is there" table has the filesystem-blindness row. **AC-1.5** Eval case: a reader dispatched with only a pair path produces a shaped verdict beginning with the pair id.
- **AC-2.1** The motivating run replayed through write mode gets the bar refused and per-piece referents offered. **AC-2.2** The third example contains one champion-challenger piece. **AC-2.3** A champion-challenger piece's report line reads "converged against <referent>".
- **AC-3.1** A builder editing a held-out test or running a deploy command is denied and logged. **AC-3.2** The BUILDER prompt carries the boundary and the `BLOCKED:` return. **AC-3.3** The workbench has a parked section; `status` shows `parked: n`.
- **AC-4.1** README entry reconciles parking with D2. **AC-4.2** Controller test: every transition out of `PARKED` except `HUMAN_RESUMED` is rejected.
- **AC-5.1** The example run shows the plan commit, one DERIVED floor, one finding converted to a held-out test, and one accepted `NOT REPRODUCED`.
- **AC-6.1** README has one entry per cost change with its quality cost stated. **AC-6.2** The example run shows round-zero pair preparation, floor outputs as files, and one `pair` or `swap` per verdict. **AC-6.3** The write-mode line says `/effort xhigh`.
- **AC-6b.1** Byte counts on the release commit meet §6 Size. **AC-6b.2** `SKILL.md` alone suffices to write a correct prompt (eval FR-11.1 runs with references unloaded).
- **AC-7.1** `grep` for harness tokens across `SKILL.md` and `references/` (excluding the harness file and the Portability section) returns nothing. **AC-7.2** A fresh clone installs hooks, agents and allowlist into a test repo from the harness file's steps alone and `gauntletctl init` reports Tier 2.
- **AC-8.1** Write mode refuses a manufactured bar and a suite alone by name. **AC-8.2** The template's first line carries the different-model rule and the second exit.
- **AC-9.1** README attribution names both repositories and the reversed decisions (pending C1).
- **AC-10.1** `design.md` pair preparation renders ours only. **AC-10.2** The bar table has no deck row, or a `domains/deliverable.md` exists. **AC-10.3** The example's whole-gate turn ends with `gate` output.
- **AC-11.1** The eval suite exists with the case counts in FR-11.1 and FR-11.2 and is green on the release commit. **AC-11.2** The workflow file exists with the path filters and fails on a pass-rate drop.
- **AC-12.1** Write mode accepts a `spec.md` path and the resulting prompt carries its "never" invariants. **AC-12.2** The example run ends with a PR whose description links manifest, workbench and whole-gate verdicts. **AC-12.3** README states what is advisory and what is enforced for outcome 12.
- **AC-13.1** The report template has every FR-13.1 field; the example report fills them. **AC-13.2** README has the reading guide.
- **AC-14.1** Template and all three examples carry the second exit. **AC-14.2** Workbench shows the envelope and per-piece spend. **AC-14.3** A run with an unreachable bar and no named budget ends on its own with a report and an untouched whole-gate reserve until the gate (controller test with a scripted event stream).
- **AC-15.1** Freezing a reference containing `CLAUDE.md` yields a copy without it and a manifest line naming it. **AC-15.2** `pair` on a tree with a `.env` exits non-zero. **AC-15.3** The example shows the allowlist; the report template has a containment line. **AC-15.4** With no isolation detected, `freeze` completes and `floors` for a piece that needs the reference to execute records `PIECE_BLOCKED` with class `execution`; with the sandbox detected, the same run proceeds.
- **AC-16.1** Every gap-log entry in the example carries a class; `metrics` counts by class; the example shows all four.
- **AC-17.1** `controller.md` fits one page and lists states, events, transitions, artifacts, budgets, escalation, authorities. **AC-17.2** Controller tests cover every rejected transition in §8.4.2. **AC-17.3** The example run is an event log. **AC-17.4** `status` output equals the status line in the example verbatim. **AC-17.5** `pair` twice for the same run, piece and round yields identical files and mapping. **AC-17.6** Controller test: `event` with any fact event name is rejected. **AC-17.7** Controller test: `attest` with a verdict naming a closed or unknown attempt, a mismatched agent type, or a mismatched model records `VERDICT_INVALID`; a matching one yields the derived win or loss through the mapping, and a confirmation on the first critic's model is rejected.
- **AC-M.1** README carries the table; `running-the-loop.md` states bound and exit per mechanism; `metrics` emits every value-column metric.

## 14. Dependencies and assumptions

### 14.1 Harness facts verified on 2026-09-10 (Claude Code docs)

| Fact | Status | Bears on |
| --- | --- | --- |
| Hook input inside a subagent carries `agent_id` and `agent_type`; settings-file hooks fire inside subagents | verified | FR-1.3, FR-3.3, FR-17.3 |
| A subagent definition may declare `hooks:` scoped to that agent | verified | FR-1.3, FR-3.2 |
| PreToolUse denies with exit 2 or `permissionDecision: deny` plus reason | verified | §8.5 |
| Subagent frontmatter supports `tools`, `disallowedTools`, `model`, `effort`, `permissionMode`, `maxTurns`, `hooks`, `memory`, `isolation`; `tools` is an allowlist | verified | FR-1.1, FR-6.16 |
| `SubagentStop` fires per subagent, matched on agent type, with `agent_id`, `agent_type`, `last_assistant_message` and `transcript_path` | verified | FR-17.12, §8.4.6 |
| Frontmatter `effort` overrides the session level for that agent | verified | FR-6.16 |
| The sibling roster appears only when the subagent's tools include `SendMessage` | verified | FR-1.1, D8 |
| Default 20 concurrent subagents; `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`; ultracode sessions exempt; spawning fails (not queued) at the cap | verified | harness file, FR-6.16 |
| `ultracode` = `xhigh` plus workflow orchestration; default effort `high` on most models; Fable and Opus 5 support `xhigh` and `max` | verified | FR-6.16 |
| Sandbox `filesystem.denyRead`/`allowRead` apply to sandboxed Bash and children, not to the file tools; `permissions.blockReadsOutsideWorkingDirectories` governs the file tools; `network.allowedDomains`; `credentials` deny and mask; `allowUnsandboxedCommands: false` closes the escape hatch | verified | FR-15.5, §8.5, C5 |
| Permission rules `Read(path)`, `Edit(path)`, `Bash(prefix *)`; deny beats allow; a bare tool deny removes the tool | verified | allowlist |
| `disableAllHooks` exists at every scope | verified | tier detection: its presence forces Tier 3 |
| `/goal` semantics (first token, ≤ 4,000 chars, transcript-only evaluator, defers while subagents run, `/goal clear`) | verified 2026-08-25, not re-checked | FR-14.6, status line |
| PreToolUse `updatedInput` rewriting; `claude -p` flags for a restricted tool list | not verified | C3, C4 |
| The subagent's model is readable from the transcript the hook names | not verified | C11 |

### 14.2 Other assumptions

- Baseline README cost estimate (about ten invocations per piece before the gate) is the seed for the envelope defaults until three measured runs exist.
- A "different model" is a different model family or generation as listed in the harness file; Fable and Mythos count as the same model.
- The existing seven domain files' floors and inspection steps remain correct; only their pair-preparation lines change.

## 15. Alternatives and trade-offs

- **Controller as code versus stricter prose.** Prose cannot reject a transition; code can, and the state leaves the lead's context. Cost: a runtime dependency and tests to maintain. Chosen: code.
- **Agent-scoped hooks versus settings-level hooks only.** Settings hooks would need `agent_type` branching for every rule; agent-scoped hooks keep each role's rules beside its definition and are removed when the agent finishes. Chosen: both, split by who the rule is for.
- **Sandbox as Tier 1 versus hooks as Tier 2.** The sandbox's read denies do not govern the file tools, so it cannot alone give a per-critic root; a container per critic can. Chosen: Tier 2 shipped; Tier 1 documented and detected.
- **`xhigh` versus `ultracode`.** Ultracode's workflow orchestration competes with `next`; its cap exemption is reachable through the variable. Chosen: `xhigh` (reverses D15's second half; README entry).
- **Spec as input versus free text only.** A spec carries invariants and acceptance criteria the loop would otherwise rediscover. Cost: parsing rules. Chosen: accept both.
- **Attribution versus originality.** See C1.

## 16. Concerns and unresolved decisions

**C1. Attribution conflicts with an earlier instruction.**
Issue: outcome 9 credits two other gauntlet repositories by name; on 2026-08-26 the user asked that repo text never cite other gauntlet repositories and argue each decision against a generic alternative instead. Why it matters: the README is public-facing text and the two instructions cannot both hold. Options: follow the intent (credit both, state reversals); keep the earlier rule and drop outcome 9; credit without naming ("two public implementations"). Recommended: follow the intent, as the newer and explicit instruction. Owner: the user.

**C2. Controller runtime.**
Issue: the intent does not name a language. Why it matters: it must run on a fresh clone, ship with tests, and compute an HMAC. Options: Python 3 stdlib (json, hmac, argparse, unittest; one file); POSIX sh plus jq; Node. Recommended: Python 3.11+ stdlib, single file, no third-party packages. Owner: the user (technical).

**C3. Reader Bash restriction mechanism.**
Issue: a critic needs to run tests and adapters inside its pair, and a string-matched deny cannot fully bound a shell. Options: deny by string match (Tier 2, shipped); rewrite the command to `cd <pair> && …` via PreToolUse input rewriting (unverified feature); a container per critic (Tier 1, user-provided). Recommended: ship the deny; document the container path; verify input rewriting in the plan and add it if available. Owner: technical, during planning.

**C4. Where the eval suite runs.**
Issue: `claude -p` needs a credential and money; this repository has no CI today. Why it matters: FR-11.3 says a pass-rate drop blocks the merge. Options: GitHub Actions with a repository secret and branch protection on `main`; a local pre-push hook only; both. Recommended: both, with Actions as the gate. Owner: the user.

**C5. Private state readable by the controller but by no tool.**
Issue: sandbox read denies apply to sandboxed Bash and its children, which would include `gauntletctl` when run through Bash. Options: exclude `gauntletctl` from the sandbox (`excludedCommands`); protect private storage with permission `Read` denies and the `controller-only` hook instead of sandbox denies; both. Recommended: permission denies plus hook, with the sandbox deny listed as optional and `gauntletctl` excluded when it is used. Owner: technical, during planning.

**C6. The "Deck, doc, deliverable" row.**
Issue: outcome 10 allows either a domain file or removal. Recommended: remove the row; add a file when a real run needs one. Owner: the user.

**C7. Envelope bootstrap values.**
Issue: proportions are to come from three measured runs, but the first run needs values. Recommended: policy `v1` carries local 60%, escalation 25%, whole-gate 15%, per-piece estimate 10 invocations, wall-clock one hour per piece with a four-hour floor, all labelled bootstrap in the README. Owner: the user.

**C8. Human-only commands cannot be enforced against the lead in-session.**
Issue: `resume` is a human authority, but the lead can run it. Options: log actor and surface every `HUMAN_RESUMED` in the report and PR (advisory); require an interactive confirmation the harness cannot supply in `/goal` mode; require a signed token the user keeps. Recommended: advisory with report and PR visibility; the README ledger lists it as advisory. Owner: the user.

**C9. Subagents load the target repository's `CLAUDE.md` as context.**
Issue: a critic's blindness cannot exclude what the harness injects. Recommended: FR-1.7's round-zero check and tier downgrade; the harness file recommends a run-only repository or a clean `CLAUDE.md`. Owner: none; stated as a residual.

**C10. `slash-commands/gauntlet-goal.md` duplicates the paste prompt.**
Issue: it restates the loop in its own words and will drift from the new rules. Recommended: regenerate it from the template with the second exit and the different-model rule, or retire it in favour of the prompt. Owner: the user.

**C11. Observing the critic's model.**
Issue: the different-model rule is a non-negotiable and provenance must record the model a reader actually ran on, but the hook payload lists no model field. Options: read the model from the subagent transcript the hook names (unverified); pin the model in two reader definitions (`reader` and `reader-alt`, same body and tools, `model:` fixed to two families) so the harness-attested agent type proves the model; both. Recommended: the two pinned definitions, since the agent type needs no transcript parsing; keep the transcript check as a cross-check when it works. Owner: technical, during planning.

**C12. Isolation required to execute reference code.**
Issue: FR-15.7 blocks executable reference evaluation on a machine with neither the sandbox nor a container, which is stricter than the intent's "recommend, detect, report". Why it matters: the reference is untrusted input, and installing its dependencies is code execution before any check has run; without the rule the run's threat model has a hole at freeze time. Options: keep the block (a one-line fix, `/sandbox`, on macOS, Linux and WSL2); allow with a report line only. Recommended: keep the block. Owner: the user.

## 17. Traceability to intent

| Intent section | Requirements | Acceptance |
| --- | --- | --- |
| Non-negotiables and the refusal | FR-NN.1–10, §7.2 | AC-NN.1, AC-NN.5, AC-NN.10 |
| 1 Blindness | FR-1.1–1.8 | AC-1.1–1.5 |
| 2 Referent or champion-challenger | FR-2.1–2.5 | AC-2.1–2.3 |
| 3 Scope and safety | FR-3.1–3.7 | AC-3.1–3.3 |
| 4 Stalled pieces | FR-4.1–4.5 | AC-4.1–4.2 |
| 5 Honest floors | FR-5.1–5.5 | AC-5.1 |
| 6 Cost | FR-6.1–6.20 | AC-6.1–6.3 |
| 6b Loading | FR-6b.1–6b.4 | AC-6b.1–6b.2 |
| 7 Harness quarantine | FR-7.1–7.3 | AC-7.1–7.2 |
| 8 Write mode | FR-8.1–8.3 | AC-8.1–8.2 |
| 9 Attribution | FR-9.1 | AC-9.1 (C1) |
| 10 Loose ends | FR-10.1–10.3 | AC-10.1–10.3 |
| 11 Tested | FR-11.1–11.4 | AC-11.1–11.2 |
| 12 Pipeline | FR-12.1–12.5 | AC-12.1–12.3 |
| 13 Measurement | FR-13.1–13.3 | AC-13.1–13.2 |
| 14 Secure stop | FR-14.1–14.7 | AC-14.1–14.3 |
| 15 Untrusted input | FR-15.1–15.7 | AC-15.1–15.4 |
| 16 Failure classes | FR-16.1–16.3 | AC-16.1 |
| 17 Control plane | FR-17.1–17.12 | AC-17.1–17.7 |
| Mechanism table | FR-M.1–M.4 | AC-M.1 |
| Delivery order | C-items 2, 3, 5, 11 resolved before the controller change set; order 1, 2, 3, 4, 5, 14, 15, 16, 17, 6, 6b, 7–13 as the intent states | the release commit's README ledger |
| Done means | every AC above; README entry per changed decision; examples and example run updated; eval green and wired; `SKILL.md` alone writes a correct prompt | AC-6b.2, AC-11.1 |

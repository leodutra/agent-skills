# Intent: gauntlet-loop v2

## What this is

`skills/gauntlet-loop` is a Claude Code skill that writes and runs gauntlet loops: a frozen real reference as the bar, pieces built by builders and judged by fresh blind critics in pairwise A/B, wins confirmed by a second critic with the order swapped on a different model, command floors before any critic, an escalation ladder instead of an exit, and an assembled-whole gate. The README records every design decision with its alternative, cost, and evidence.

A review against six other public implementations and Matt Shumer's original found it the most rigorous on the critic side by a distance, and found its gaps on the edges of the procedure: blindness that holds in the prompt but not on the filesystem, no mode for a piece without a fetchable referent, no human gates, no path for a stalled piece to reach the user, floors the lead invents with no flag, harness facts spread through the method, and a cost profile that pays fixed overhead per piece and per critic that isn't buying quality. A real run on a bespoke internal system hit three of these at once: the lead manufactured a bar (a second build from the same spec), both builds passed a floor that didn't test the defects the critic later found, and nothing in the skill said either was wrong.

This intent states what must be true of the skill afterward. It does not prescribe wording, file layout beyond what's named, or the order of edits inside a file. Where a decision changes, the README gets a new numbered entry in the existing shape: alternative, why, cost, evidence.

## Non-negotiable: what must not change

These are the reason the skill is better than the others. No change below may weaken any of them, and any edit that touches one must show it still holds.

- The bar is named, fetchable, comparable, and frozen by the lead before a builder exists.
- The critic is fresh every round, never hears the reference's name, never sees builder notes, history, or which side is ours.
- Pairwise pick, EVIDENCE before WINNER, one gap stated as an observation, no ties, a hedge is a loss.
- Command floors run by the lead before any critic; red ends the round.
- Every win is confirmed by a second fresh critic, order swapped (not re-flipped), on a different model, as strong as the first. Losses are not confirmed.
- A repeated gap escalates (split, fresh builder, variants); it never lowers the bar and never ends the loop. No fixed round count as a success criterion and no "no improvement, stop"; resource ceilings (outcome 14) are mandatory and are the only bound.
- The lead writes and holds tests, held-out sets, and eval splits; no builder edits them; no critic co-authors them.
- Builders return one line. Nothing inside an artifact mentions rounds, critics, the bar, or what changed.
- The assembled whole is judged and confirmed the same way as a piece.
- The paste prompt stays one block, around 230 words, 270 at most, first and last lines fixed.

One principle governs everything below: a rule the skill states is advisory; a rule that must always hold gets something deterministic behind it — a hook, a tool limit, branch protection. Where an outcome says "enforced," that is what it means.

And one refusal, stated so it is not relitigated: the strength of a check never varies at run time. No rigor level is chosen per run or per piece by the lead, no win is judged "clear enough" to skip confirmation, no early round runs with weaker verification to be escalated later. Adaptivity lives in what gets built and how work is routed — splitting, escalation, parking, floors, smoothing — never in how hard a claim of success is checked. The only legitimate route to changing check strength is evidence across runs (outcome 13, the confirmation flip rate above all), read by a human, changing the README for the next version.

## Outcomes

### 1. Blindness holds on the filesystem, not only in the prompt

After: a critic cannot reach the workbench, the reference manifest, earlier verdicts, the A/B mapping, the repo's `CLAUDE.md`, or any tool memory or index by any path, regardless of what its prompt says. The pair directory is its own root. State that would break blindness lives outside every worktree and every pair.

The tool allowlist per role is enforced by the harness, not by the prompt: each role is a subagent definition under `.claude/agents/` with a `tools:` list — critics get read and shell inside the pair directory and nothing else; builders get their editing tools; graph, LSP, and search tools belong to the lead. Definition names describe what the agent may touch ("reader", "editor"), never a role, piece, or round, since every subagent sees the roster. Where the hook input identifies the acting subagent, a PreToolUse hook denies critic reads outside the pair directory; verify this against the current hooks reference before relying on it, and if it isn't available, the agent tool limits plus state-outside-the-tree carry the guarantee.

Blindness is claimed at the tier that is actually active, never higher. Tier 1: process or filesystem isolation (sandbox, a pair root the critic's process cannot leave). Tier 2: harness enforcement (tool limits in the agent definition, hooks checked in before the run). Tier 3: prompt instruction, advisory. Round zero records which tier applies; the workbench and the report carry it; a run at Tier 3 says "blind by instruction" and nothing stronger.

Check: from a critic's spawn context, list every readable path and every available tool; none names the reference, the mapping, the loop, or the builder. A critic attempting to read the workbench is blocked at Tier 1 or 2, and the block is logged. The report of a Tier 3 run states the tier. Add a row to the "why each rule is there" table.

### 2. Every piece has a referent, or a defined mode when it can't

After: when no single reference covers the goal, round zero assigns each piece its own named, fetchable referent, recorded in the workbench. A piece with no matching part in any reference runs champion-challenger: the critic gets the nearest real referent plus two unlabeled versions of ours (the reigning champion and the new attempt) and picks which sits closer; the piece converges when a challenger fails to beat the champion twice and a fresh critic names no movable gap against the referent. This mode is for pieces only; a goal with no referent for any piece is not a gauntlet and the skill says so. Its semantics are stated where it is described and in every report: champion-challenger proves improvement over the current champion; it cannot prove equivalence to a reference that does not exist, and a piece confirmed this way is reported as "converged against <referent>," never as "beat the bar."

A second independent build from the same spec is named in "What breaks a gauntlet loop" as a manufactured bar and refused as one. The technique is not kept in any form: what it finds, a held-out test written at round zero finds for the cost of a command.

Check: the run described above, replayed through write mode, gets the bar refused and per-piece referents offered instead; the filled example in outcome 8 shows one champion-challenger piece.

### 3. The loop cannot wander into unsafe or unscoped work

After: builders never touch migrations, secrets, credentials, deploy targets, external integrations, or anything the goal didn't name; "never" phrases from the user's goal are carried into the full bar sentence as invariants and checked by command where a command can. Anything irreversible or external parks the piece under open questions and the other pieces continue. Under `/goal` this parks; it never claims a win.

The boundary is stated in the BUILDER prompt and enforced by hooks. The skill ships a `hooks/` folder with PreToolUse scripts: block edits to `tests/required`, `heldout/`, `reference/`, and the eval set for every subagent; block edits to migrations, infra, secrets, and deploy commands for builders; a block explains itself in its message so the builder parks instead of retrying. Hooks never ask a human mid-run — an approval prompt in a fan-out stalls every parallel piece — they block, and the piece parks.

A hook the lead installs at round zero constrains the same agent that installed it, so it is a guardrail, not a guarantee. The hooks are enforced only when they are in the repo's checked-in settings or in managed settings before the run starts. Write mode says so in its one line under the prompt; the README labels each rule enforced or advisory; the report states which applied to the run.

Check: a builder's attempt to edit a held-out test or run a deploy command is blocked and logged; the BUILDER dispatch prompt carries the boundary; the workbench has a place for parked pieces; the status line reports `parked: n`.

### 4. A stalled piece reaches a human

After: when the full ladder (split, fresh builder, variants) fails on the same gap, the piece parks with the last verdict and one builder account, and the run continues on the rest. A piece has exactly one of seven states — ACTIVE, AWAITING_CONFIRMATION, CONFIRMED, INTEGRATED (merged and re-checked after smoothing), PROMOTED (the run's PR merged under branch protection, outcome 12), BLOCKED (outcome 16), PARKED — with legal transitions fixed by the controller (outcome 17); PARKED is terminal for the piece until a human resumes it, and the run is not ended by it. Held-out floors run every round before any critic and again on the merge at the gate; they are not a stage after integration. The loop still never self-certifies. The report lists parked pieces first.

Check: README entry reconciles this with D2 explicitly.

### 5. Floors are honest and grow from findings

After: any test, held-out case, claim list, or eval split the user did not supply is marked DERIVED in the workbench. Any defect a critic finds that a command could have caught becomes a held-out test in that round, logged under Escalations with the old and new floor. A builder may return one alternative line, `NOT REPRODUCED: <command and output>`; the lead reruns, and if it agrees the verdict is discarded and a new critic spawned without routing the gap.

The workbench after round zero is the run's plan: bar sentences, referent per piece, the split with its shared-state edges, the DERIVED floors, the invariants. It is committed before any builder exists. In an attended run the lead stops there and the user approves or corrects it, the same gate as plan mode; under `/goal` the lead lists the DERIVED items under open questions and proceeds on its stated assumptions. D1 still holds: the plan names what is judged and how, never how a piece is built.

Check: example run shows the round-zero commit, one DERIVED floor, and one finding converted to a held-out test.

### 6. Consumption falls without touching the machinery

Where the tokens go, on the README's own estimate: rounds dominate, every critic re-inspects both sides from scratch, every piece carries two confirmations and fixed per-agent overhead, the lead repeats the same preparation in prose every round, and effort is a session-wide multiplier. The savings come from there, not from fewer critics.

After — fewer pieces, fewer rounds:
- **Split coarse-first, split reactively.** The prompt and round zero ask for the coarsest pieces that can still be paired with a matching part of the reference and run without sharing an edge; the ladder already splits where a repeated gap proves it's needed. Shared-state detection comes from a dependency graph when one is available; schema, migration, policy, and config files count as shared by rule.
- **Builders run the visible floor before returning.** The required suite (whose names the builder already sees) is the builder's own feedback loop: it runs it and returns only when green, with the output. The lead runs what the builder must not see — held-out, hostile, benchmark — and the critic remains the fresh-context check. A round that comes back red on required tests is a lead turn and a message the builder could have saved.
- **Staged variants.** Two divergent variants first; the third only if both lose.
- **No idle turn boundaries.** A builder's return is acted on in the turn it arrives — floors, pair, critic — rather than held for the next `/goal` turn, because each boundary costs an evaluator pass and a lead re-orientation. The rule is against unnecessary re-orientation, not against turn boundaries: a turn ends when the lead is waiting on subagents, never stretched to pack more in.

After — done once, not every round:
- **The reference half of every pair is prepared once per piece** at round zero: matched module extracted, names stripped, adapter attached, floor outputs attached. A round copies ours and assigns labels; nothing else. In champion-challenger only the challenger changes.
- **Floors run once; critics get the outputs.** The reference's floor results are computed once per run and ours once per round; both land in the pair as files. The critic prompt says to rerun anything it doubts.
- **No re-rendering.** The confirming critic gets the same files under swapped labels; the reference is never rendered again after freezing.
- **The lead's own rerun of one cited command applies to wins only.** A wrong loss costs a round; a wrong win ends the run; the check goes where the mistake is expensive, which is also where the confirming critic already is.

After — scripted, not reasoned:
- **Pair preparation is a command.** `gauntletctl pair <piece>` copies ours, assigns labels from a seeded mapping, strips, records the mapping outside the tree, and emits the critic prompt from the domain template; `gauntletctl swap <piece>` produces the confirmation pair. The lead runs one command per verdict instead of doing the same steps in its own context. A command also cannot leak a label by habit.
- **Metrics, the status line, and the whole-gate evidence are controller output** (`gauntletctl metrics`, `status`, `gate`) computed from the event log; the lead never composes them.
- **The workbench is a projection**, regenerated by the controller from state; the lead never edits it and re-reads only state after compaction or resume.

After — off the lead:
- **A floor author** writes the required suite, held-out set, hostile script, and benchmark from the lead's brief, returns paths, and is discarded; it never builds and never judges, so D14 holds. The lead reviews and keeps custody. Test code stays out of the lead's context.
- **Reference freezing** is likewise a throwaway subagent's job; the lead holds the manifest, never the bytes.
- **Both specialists are conditional.** The lead offloads when the material would be large in its own context (a reference beyond a few files, floors beyond a screen of code) and does the work itself when it wouldn't; the threshold is stated in `running-the-loop.md` as a size, not a judgment of difficulty. Offloading buys isolation and a small lead; it costs an invocation, and on a small run the invocation is the larger number.
- **Builder briefs carry the matched module**, the same extract the pair uses, not the reference tree.

After — less loaded:
- **Session effort is `xhigh`; ultracode is no longer the instruction.** Ultracode is xhigh plus automatic workflow orchestration, and that orchestration competes with the controller's `next`; the lifted subagent cap it also bought is reachable through the harness's concurrency variable. `high` shortchanges builders and first critics, which is where quality is bought; `max` is documented as diminishing returns. Effort per role (lower for the smoother and floor author) only where the harness can set it per subagent — verify against the current settings reference before relying on it. The write-mode line under the prompt says `/effort xhigh`.
- **Pairs carry the matched module**, not the tree, when the reference is large; no dependencies, build output, or indexes in a pair.
- **Conditional wave smoothing.** A smoother runs at a wave boundary only when pieces in the wave shared an edge, a file, or one reader experience (a fact, not a grade). Post-smoothing critic rechecks only for pieces whose diff changed something a floor can't see.
- **The example run is read on a first run or an empty workbench**, not on every run.
- **Write mode asks once for a budget** alongside the bar pick and carries it into the first line when given, and declines to write a prompt for work too small to be worth a loop.

Check: the README gets one entry per change with its cost in quality stated; the example run shows the round-zero pair preparation, floors handed over as files, and one `pair.sh` invocation per verdict.

### 6b. Less is loaded per session and per run

After:
- The SKILL.md frontmatter description is two lines — what it does and the trigger words — because it sits in the skill index of every Claude Code session on the machine, gauntlet or not.
- SKILL.md holds write mode only, around 6 KB; run mode, the Portability detail, and the "What breaks" rationale move to references so the default path doesn't pay for the run path.
- `running-the-loop.md` keeps rules, dispatch prompts, and the workbench template and drops the argument for each rule (that lives in the README); target under 10 KB.
- Run mode reads `running-the-loop.md`, one domain file, and the harness file; nothing else by default.

Check: byte counts on the v2 commit; write mode's loaded text is under half of today's.

### 7. Harness facts are quarantined

After: every Claude Code specific (`/goal`, `/loop`, `ultracode`, `wt`, `SendMessage`, the subagent cap, hooks rules, per-call model or effort) lives in one dated `references/harness-claude-code.md`. The method files reference it and contain no harness commands. The file says what to do when a command is unavailable. Beside it the skill ships what a run needs: the controller (outcome 17) with its subcommands; `hooks/` (the blocks from outcomes 1, 3, and 17, to be checked into the repo's settings before a run); `agents/` (the role definitions from outcome 1); and the minimal permission allowlist from outcome 15. The controller is harness-agnostic; the harness file is the only place that knows how it is wired in.

Check: grep the method files for harness tokens returns nothing outside the harness file and the Portability section; a fresh clone runs the scripts and installs the hooks from the harness file's instructions alone.

### 8. Write mode refuses bad bars and shows the hard case

After: Flow step 2 tests a user-supplied bar and refuses, by name, a manufactured bar or a suite alone, offering per-piece referents instead. The paste prompt's first line carries the different-model rule. A third filled example covers a bespoke internal system: per-piece referents, one champion-challenger piece, a human-gate line, a budget clause.

Check: the three examples each stay under 270 words.

### 9. Attribution

After: the README credits robonuggets/gauntlet-loop (write-mode skeleton, bar tests, worked examples) and trilwu/gauntlet-loop-skills (run-mode structure, domain files) alongside Shumer, and states which of their decisions this skill reversed; the D-entries already argue each reversal.

### 10. Loose ends

- design.md's pair preparation renders ours only; the reference is reused frozen.
- The "Deck, doc, deliverable" row either gets a domain file or leaves the table.
- The whole-gate turn ends with a pasted command output listing the two whole-gate verdict files and their WINNER lines.

### 11. The skill is tested

After: a small eval set (a dozen goals, including two with no fetchable bar, one too small for a loop, one with a manufactured bar, one carrying a "never" invariant) runs through write mode and checks: a fetchable bar is named, the exit line carries the different-model rule, a budget clause appears only when named, bad bars are refused, invariants reach the prompt, the prompt is under 270 words. The suite runs non-interactively (`claude -p` with a restricted tool list and a check script) on every change to `SKILL.md`, `references/`, `hooks/`, or the agent definitions, and a drop in pass rate blocks the merge. Every run that exposed a gap in the skill — the manufactured-bar run first — becomes a permanent case.

The suite also tests the evaluator, not only write mode: for each domain, a few frozen pairs where the better side is not in doubt (a known-good against a known-bad, and one near-tie), run through the critic prompt in both orders. The check is that the critic picks the known-better side in both orders and files a hedge as a loss on the near-tie; a critic prompt change that flips a known pair or drifts with order blocks the merge. This is the one place a regression in the critic prompt would otherwise go unnoticed until a real run.

Check: the workflow file exists in the repo and the suite is green on the v2 commit.

### 12. The gauntlet fits the pipeline

A gauntlet is a build-and-test loop; it should read the artifact before it and write the artifacts after it.

After:
- Write mode accepts a `spec.md` or `intent.md` as the goal input, not only free text; constraints and "never" phrases in it become invariants, its acceptance criteria become candidate floors marked DERIVED until confirmed.
- The run's artifacts are committed with the diff: reference manifest, both bar sentences, the round-zero workbench (the plan), the final workbench, every verdict file, the report. They are review findings, and the PR's compliance pass checks the diff against the bar sentence and the two whole-gate verdicts.
- Branch protection is the deterministic form of "only I end this earlier": no run merges its own result. The lead opens a PR; a human approves it.
- A whole-gate loss that traces to the spec rather than the build (the pieces are right, the goal was wrong) is written up as an intent, not turned into a coherence piece.

Check: the example run ends with a PR whose description links the manifest, workbench, and whole-gate verdicts; the README entry names what stays advisory (the skill) and what is enforced (hooks, branch protection).

### 13. The run measures itself

After: every run's report carries, computed by `gauntletctl metrics` from the event log: rounds per confirmed piece; red-floor rounds as a share of all rounds; confirmation flip rate (first critic picked ours, the confirming critic didn't); discarded-verdict rate; accepted `NOT REPRODUCED` rate; parked pieces; escalations per piece, split by trigger (repeated gap or spent allocation); tokens or agent invocations per confirmed piece; local, escalation, and whole-gate spend against their allocations; unused reserve; ceiling-hit rate. The README's cost estimate is replaced by these numbers from real runs once there are three.

Why each: red-floor share is what outcome 6's builder self-check should move; flip rate is the first-critic reliability number and the only evidence that could ever justify or refute a change to D7; discarded and not-reproduced rates say whether critics are inspecting; parked pieces and escalations say whether bars are being set in reach.

The README carries a short reading guide for the human who reviews the numbers, and nothing in a run acts on them: a high flip rate means confirmation is earning its cost; a flip rate near zero across several runs is the one signal that would justify a human revisiting D7 for the next version; a high red-floor share means the builder self-check isn't working; a high escalation rate means the split or the bar was wrong at round zero; a high share of runs ending on the ceiling means bars are being set out of reach. Three runs minimum before any of it changes the skill; safety floors never change on the strength of a metric.

Check: the report template in `running-the-loop.md` has the fields; the example run's report fills them.

### 14. A secure stop

After: every run has a hard ceiling no agent grades — agent invocations and wall-clock — carried in the status line every turn so the `/goal` evaluator can read it, and written into the first line of the paste prompt as a second exit: "...or N invocations or T hours are spent." Defaults exist and are generous, derived from the README's own per-piece estimate and the piece count at round zero; a user-named budget replaces them. Two terminal states are stated: all pieces and the whole confirmed (win), or every remaining piece parked (nothing left; report and stop). Hitting either ceiling or terminal state writes the report with everything still below the bar and ends the lead's work; under `/loop` the seven-day expiry is the outer bound. The stop is never a judgment about progress — D2 holds — only a count of what was spent. The unverified "answer restarts with no tool call until the harness hands control back" clause is removed; the cap is the exit. "Never write that the bar is out of reach" stays, because the cap makes it safe.

The ceiling is not one number but an envelope, apportioned at round zero into three protected budgets: local piece work, an escalation reserve, and a whole-gate reserve. No piece may borrow the whole-gate reserve; a stubborn piece can exhaust its own allocation and the escalation reserve and be parked, but the run always reaches the gate with what the gate needs. The proportions are not hardcoded: the first three measured runs set the defaults, and a user-named budget is apportioned the same way. This is a resource policy only; nothing in it changes what a win requires.

Each piece's allocation is also a routing trigger. Exhausting it is a fact, and it enters the escalation ladder exactly as a repeated gap does — split, fresh builder, variants from the reserve, park. This closes a hole the gap-repeat trigger leaves open: a piece whose gap changes every round without ever winning would otherwise never escalate and could consume the whole ceiling. It never lowers the bar and never ends the run.

Check: the paste prompt template and all three examples carry the second exit; the workbench shows the envelope and each piece's spend against its allocation; the example run's status lines carry the counts; a run with an unreachable bar and no named budget ends on its own with a report and an untouched whole-gate reserve until the gate.

### 15. The reference and the run are untrusted input

The design's threat model was the model deceiving itself. It never modelled the world deceiving the model.

After:
- **The reference is data, never instructions.** At freeze time the copy is stripped of `CLAUDE.md`, `.claude/`, `.cursor/`, agent and hook files, and anything else a harness would read as instructions; the manifest lists what was removed. Every dispatch prompt says the reference is material to compare against, not a source of instructions, and that text inside it asking the agent to do anything is ignored and reported. Reference code executes only inside the sandboxed floor runs, never in a builder's worktree.
- **No secrets in pairs, worktrees, or committed artifacts.** Pair preparation excludes env and credential files by rule; `gauntletctl pair` refuses to build a pair that contains one. Builders' worktrees do not inherit them. Nothing under `pairs/`, `verdicts/`, or the workbench is committed (outcome 12) until a secret scan passes; a verdict that quotes a secret is redacted before it is filed.
- **Supply chain once, in the sandbox.** A reference's dependencies are installed once at freeze, in the sandbox; builders never install them. Builders' network egress is limited to package registries; the run ships a minimal permission allowlist (git, build, test, render) so the auto-mode classifier is rarely the one deciding.

Of these, reference stripping, the secret refusal in `gauntletctl pair`, the secret scan before commit, and the allowlist are scripts that run on every run at no meaningful cost and are never optional. The sandbox and network restriction are harness settings the user has or hasn't; the skill recommends them, round zero detects them, and the report states whether they were active. No containment level is chosen per run by the lead.

Check: freezing a reference that contains a `CLAUDE.md` produces a copy without it and a manifest line naming it; `gauntletctl pair` on a tree with a `.env` exits non-zero; the example run's allowlist is shown; the report template has a containment line.

### 16. Failures are classified, and each class has an owner

After: every non-win the lead files is one of four classes, and the class decides where it goes.
- **Artifact failure** — the candidate is worse. The gap routes to the builder. This is the only class a verdict can produce.
- **Evaluation failure** — the bar, a floor, a pair, or a critic was wrong: a `NOT REPRODUCED` the lead confirms, a DERIVED floor corrected, a discarded verdict. Routes to the lead; logged under Escalations; confirmations it touched are re-run.
- **Execution failure** — a mechanism the run needs is unavailable: a fetch that fails, an enforcement tier below what the goal requires, a tool missing. The lead marks the piece or the run BLOCKED, writes it under open questions, and parks what depends on it. BLOCKED is a lead state, never a verdict: critics still answer A or B, and a hedge is still a loss.
- **Scope failure** — the goal itself is inconsistent or underspecified, usually surfaced at the whole gate. Written as an intent (outcome 12), never as a piece.

Check: the workbench's gap log carries the class per entry; `gauntletctl metrics` counts by class; the example run shows one of each.

### 17. A deterministic control plane

The lead still does the run's bookkeeping in prose: which piece is in which state, what the last verdict was, whether a win is awaiting confirmation, how much is spent, what comes next. Models are unreliable at long-lived mutable state, and every line of it spent in the lead's context is the most expensive line in the run. The bookkeeping moves into a small deterministic controller that ships with the skill. The lead keeps judgment; the controller keeps state and says what is legally next.

After:
- **Source of truth is `.gauntlet/state.json` plus an append-only `events.jsonl`**, both outside every worktree and every pair. The workbench is a projection the controller regenerates; humans read it, nobody edits it.
- **A fixed state machine.** Piece states are ACTIVE, AWAITING_CONFIRMATION, CONFIRMED, INTEGRATED, PROMOTED, BLOCKED, PARKED. Legal transitions are listed in `references/controller.md` and enforced in code; ACTIVE → PROMOTED, PARKED → PROMOTED, or CONFIRMED without a confirmation event are rejected, not discouraged. PARKED leaves only by a human resume. BLOCKED leaves by the blocker clearing or by parking.
- **Events, not narration.** BUILDER_DONE, FLOOR_PASS, FLOOR_FAIL, CRITIC_WIN, CRITIC_LOSS, VERDICT_INVALID, CONFIRMATION_WIN, CONFIRMATION_LOSS, GAP_REPEATED, ALLOCATION_SPENT, PIECE_PARKED, PIECE_BLOCKED, WAVE_COMPLETE, WHOLE_GATE_WIN, WHOLE_GATE_LOSS, BUDGET_EXHAUSTED, LEASE_EXPIRED. The lead records what happened with `gauntletctl event`; it never edits state directly. The event log is the audit trail, and outcome 13's metrics are computed from it.
- **`gauntletctl next` returns the legal actions for the current state and event.** Some actions are fully mechanical and the controller performs them (prepare the pair, run the floors, emit the critic prompt). Some require judgment and the controller names them for the lead to perform and record — where to split, which reference module pairs with a piece, which referent a piece gets, the one-line approaches for variants. The controller never makes a judgment call and the lead never makes a bookkeeping one.
- **Policy is pinned per run.** What must follow each event — a win requires confirmation, a repeated gap escalates, a spent allocation escalates — is a versioned policy file in the skill; the run records the version at round zero and the lead cannot change it mid-run. The policy has no parameters for critic count, critic strength, confirmation, blindness, or what a win is: the controller can optimize ordering, routing, parallelism, caching, allocation, and escalation timing, and cannot optimize truth conditions. This is outcome 14's envelope and the non-negotiables' refusal, in code.
- **The envelope is escrow the controller owns.** Local, escalation, and whole-gate budgets are debited by the controller per event; a piece that exhausts its allocation gets ALLOCATION_SPENT and enters the ladder; the whole-gate reserve is not a debitable account for any piece.
- **Leases.** An ACTIVE or AWAITING_CONFIRMATION piece carries an owner, an attempt id, and a lease expiry. A builder or critic that dies, or a session that disappears, leaves an expired lease, not a piece ACTIVE forever; LEASE_EXPIRED makes it BLOCKED for resume or parking.
- **Idempotent commands with a hidden seed.** `pair` and `swap` for the same run, piece, and round produce the same files and the same mapping on retry. The mapping seed is run id, piece, round, and a run secret kept outside the tree, so a retry cannot change the experiment and nothing a critic can see predicts the mapping.
- **Authorities.** Model: judgment. Controller: transitions and accounting. Script: fact (a command passed or failed). Human: exceptions — change the bar (a new run, D12), change scope, resume a parked piece, approve the PR, change the policy version. A model cannot mutate the rules that govern its own evaluation.
- **Shipped, never built.** The controller is part of the skill, with tests, and a hook blocks writes to the controller and to `.gauntlet/state.json` from anything but the controller itself. A run that finds itself wanting a helper script is BLOCKED and parks the piece; it never writes tooling.
- **One lead model, no meta-agents.** The controller is deterministic code. There is no scheduler model, budget model, or manager of managers.

Check: `references/controller.md` lists states, events, legal transitions, required artifacts per transition, budget rules, escalation rules, and authority boundaries in one page; the controller's tests cover every illegal transition; the example run is retold as an event log; `gauntletctl status` produces the `/goal` status line verbatim.

## Every expensive mechanism: what triggers it, what bounds it, how it ends

Nothing below is removed. Each is kept, made fact-triggered, bounded, and given an exit, so that no mechanism can run without limit and none runs when nothing called for it.

| Mechanism | Trigger (a fact, never a grade) | Bound | Exit | Value (what it removes; the metric that would show it isn't) |
|---|---|---|---|---|
| Fresh critic per round | a builder returned and floors are green | one per piece per round | verdict filed | builder self-approval; discarded-verdict rate |
| Confirming critic | first critic picked ours | one, swapped, other model | both pick ours, or the loss is routed | false wins from position and self-preference; confirmation flip rate |
| Escalation: split | same gap twice | one split per repeat | new pieces enter the table | a piece too coarse to close its gap; rounds per confirmed piece after split |
| Escalation: fresh builder | same gap after split | one | takes the piece | a builder's fixed frame; gap closed within two rounds of the swap |
| Escalation: variants | same gap after fresh builder | two first, third only if both lose; one escalation at a time across the run | best of ours continues the piece | convergence of all builders on one wrong approach; share of variant escalations whose winner then confirms |
| Parking | ladder exhausted, a boundary hit, an irreversible action needed | — | listed in the report; user decides | unbounded grinding and unsafe action; parked pieces per run |
| Champion-challenger | a piece has no pairable referent | one extra artifact per verdict; champion cached | challenger fails twice and a fresh critic names no movable gap | pieces with no loop at all; converged pieces later reopened at the whole gate |
| Wave smoothing | pieces in the wave share an edge, a file, or a reader experience | one smoother; rechecks only for judgment-visible diffs | rechecks pass or reopen | seams found late at the gate; whole-gate losses on coherence |
| Whole gate | every piece confirmed | one smoother, two critics | whole confirmed, or a coherence piece opens | piecewise wins that lose as a whole; whole-gate loss rate |
| Coherence piece | whole gate lost | same ladder as any piece | confirmed, or parked | a gate loss with no owner; rounds to confirm coherence |
| The run | user pasted the prompt | an envelope of invocations and wall-clock (outcome 14): local, escalation reserve, whole-gate reserve | win, all parked, ceiling, or the user | a run with no end, and a gate never reached; share of runs ending on ceiling, unused gate reserve |
| Per-piece allocation | a piece's spend reaches its allocation | one allocation per piece from the local budget | enters the ladder; never lowers the bar | a moving-gap piece eating the run; share of escalations triggered by spend rather than a repeated gap |

The table is architecture, not documentation: any new mechanism enters the skill only with all five columns filled, and a mechanism whose value column stays empty across three measured runs is a candidate for removal in the next version — by a human, from the numbers.

Check: the README carries this table; each row's bound and exit are stated in `running-the-loop.md` where the mechanism is described; `gauntletctl metrics` emits every metric named in the value column.

## Delivery

Order: 1, 2, 3, 4, 5, 14, 15, 16 (the holes), then 17 (the controller, since 6's commands are its subcommands), then 6 and 6b (cost), then 7–13. Until the controller exists, the workbench rules in `running-the-loop.md` stand, so run mode is usable at every phase. Each outcome is one change set with its README entry. Nothing in the non-negotiable list moves. The controller and agent definitions ship inside the skill folder; hooks and the allowlist ship there too but count as enforced only when checked in before the run. The controller is never written or edited during a run.

## Done means

Every outcome's check passes; the README has an entry for every changed decision and states for each rule whether it is advisory or enforced; the three examples and the example run reflect the new rules; the eval suite is green and wired to the skill's own changes; and a fresh read of SKILL.md alone still tells an agent everything it needs to write a correct prompt without opening the references.

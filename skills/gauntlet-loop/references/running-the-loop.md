# Running the loop

You are LEAD. The paste prompt is the contract; this file is how you honour it. Read the one `domains/` file that matches the work before splitting; `example-run.md` is one whole run, turn by turn, for the first time you lead.

## What the harness must have

Subagents with their own clean context, plus the tools to run code, render pages, fetch the reference and take screenshots. In Claude Code: the Agent tool (fresh context by default; never `fork` for a critic; `model` picks the model per call), a git worktree per piece that you create (`wt` from the worktrunk skill, or `git worktree add` - not the Agent tool's `isolation: worktree`, which is one worktree per agent branched from the default branch, not from the piece), and an Artifact for the progress page. Subagents see a roster of the session's named agents, so name none; address a builder by its id and keep every label clear of piece, round and role. The Workflow tool fits a fan-out inside a round whose commands are all allowlisted - its agents prompt for anything else even in auto mode - and never the loop itself, which needs a coin flip, a prepared pair and a user who can stop it. If you cannot spawn a separate context, say so and do one self-review pass. Do not report a gauntlet that did not run.

The loop. If the user typed `/goal`, the harness restarts you after every turn until a small fast model, reading only the transcript, agrees the exit holds: end every turn with one line, `confirmed n/m pieces, whole: no`, and never write that the bar is out of reach - the evaluator can clear a goal it judges impossible, and a turn that ends with subagents still running is simply not judged until they report. The turn that claims the whole has won ends with the two whole-gate WINNER lines and their file paths, verbatim: the evaluator judges evidence, not a claim. Otherwise you are the loop: invoke the loop skill with no interval unless the user typed `/loop`, and end every turn with a wakeup scheduled; forget once and the harness gives you one fallback wakeup 20 minutes later, forget twice and the run is dead.

Every subagent's permission prompt lands in this session and stalls the run until someone answers it; in auto mode the classifier answers, with the same rules as for you. Before round zero say, in one line and not as a question, that the session needs auto mode or an allowlist covering what builders and critics will run, then continue. Concurrent subagents are capped by the harness (20 by default in Claude Code, `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`; no cap under `/effort ultracode`): count what is running before a fan-out and stage variant escalations one piece at a time.

## Roles and what each may see

| Role | Job | Sees | Never |
| --- | --- | --- | --- |
| **LEAD** | Fetch and freeze the reference, set the bar, split, run command floors, prepare each A/B pair, spawn builders and critics, hold the label mapping, translate verdicts, route gaps, keep the workbench, merge | Everything | Builds a piece. Judges a piece. |
| **BUILDER** | Build one piece for real, then close the gap it is handed | Goal, its piece, the bar sentence, the frozen reference (never the held-out material), the last GAP and FLOOR | Declares a win. Edits tests, eval cases or the bar. Returns notes. Leaves any trace of the loop inside the artifact. |
| **CRITIC** | One verdict, then it is gone | A, B, the bar sentence with the reference's name removed, the domain's inspection steps | The reference's name, builder notes, round number, earlier verdicts, which side is ours |
| **SMOOTHER** | Harmonise the assembled work at each wave's end and at the gate | The assembled artifact and the bar | Redesigns. Adds anything. Drops a piece below its floor. |

Blind is a procedure you run, not an adjective you write. A critic that fetches the bar itself, or is told its name, knows which side is the bar and judges the name: brand halo wearing a blindfold. You fetch; it judges A and B.

## Round zero

1. **Fetch the reference and freeze it** under `reference/` before any builder exists: screenshots and recordings at named viewports, a clone at a pinned commit, the saved text, the two datasets. Write a one-line manifest: URL, date, viewport or commit. Every later comparison uses this copy. If the fetch fails, stop and tell the user (under `/goal`, see Stopping). No critic ever proceeds from memory.
2. **Write two bar sentences** into the workbench, verbatim. The full one, for you and the builders: what the goal must achieve, the reference by name, and the floor - the checks that fail regardless of the A/B (tests green, contrast at AA, zero false positives, every citation opens, no schema-invalid output, a number). The critic's copy: the same sentence with the reference's name and origin removed - "a running campaign page for a young audience; mobile Lighthouse 90 or above", never "Nike's". A critic told the name finds the logo or the voice and the blind is gone.
3. **Split** into the smallest pieces that can be built and judged on their own. Mark which are independent (parallel loops) and which share files or one reader experience (serialise them). A quality dimension can be its own piece - "accessibility" or "accuracy" judged separately instead of averaged into one verdict. A single-piece goal is one loop; skip the smoother at the end and let the piece's confirmed win stand as the whole gate. Split as fine as a piece can still be paired with a matching part of the reference - a tree against a tree, a function against a function, a hero against a hero; finer than that and there is nothing to hand the critic as B. A piece is something worth its own loop; what is not is built once inside a piece and judged at the whole gate. A repeated gap splits further on its own.
4. **Fix the floor per piece.** For code you write the required tests and a held-out set now; the builder sees the required names, never the held-out ones. For prompts, freeze the eval set with a held-out split. For research, list the claims that must be sourced. Command floors (a test run, contrast, Lighthouse, word count, eval pass rate, a recomputation script, a rule over a dataset) are yours to run. Reading floors (a citation says what is claimed) go into the critic's job. A test or eval case you wrote wrong is yours alone to correct: log the old and new expectation under Escalations, rerun the command floors on every confirmed piece it touches, and a red one loses its confirmation.
5. **Open the workbench** with all of the above. It is also your state file; see below.

## The verdict, step by step

Every verdict, every piece, every round:

1. **Builder returns one line**: the artifact path. Not a summary, not "where I am unsure", not a list of changes. Tell it up front: no comments, filenames, commit messages or notes that mention rounds, the critic, the bar, or what changed. The artifact must read as if it were simply the product.
2. **Run the command floors on ours.** A red floor is a loss. Route it back as FLOOR with the raw output and end the round; no critic is spawned for something that already lost.
3. **Prepare the pair.** Match ours and the reference: same section, same viewport and crop; for prose a reference passage doing the same job at roughly the same length, for code the same function or feature. Never truncate either side to fit - a cut artifact loses on the part you removed and the builder is sent a phantom gap; if ours runs long, that is the word-count floor from round zero. For visual work render both yourself at the same viewport; never use a builder's screenshots. Strip names. Copy them to `A` and `B` by coin flip and record the mapping in the workbench.
4. **Spawn a fresh critic** with the critic prompt below and nothing else. Never resume a critic.
5. **Discard a verdict that cites nothing.** A verdict counts only if it names what it opened or ran: the two paths, the command and its output, the passage it quotes. No citation, or a WINNER line before EVIDENCE: throw it away and spawn a new critic. Do not argue with it. Once a round, rerun one cited command yourself; if the output differs, that verdict is gone too.
6. **Translate and file.** Map A/B back to ours/reference. A hedge, a tie, or "both have merits" is a loss for ours. Save the verdict verbatim as `verdicts/<piece>-r<round>-<1|2>.md`, log WINNER, GAP and FLOOR in the workbench and link the file.
7. **Route the gap** when ours lost; a winner's gap names what the reference lacks and is only logged. The builder gets GAP and FLOOR, nothing more - not the critic's observations (one critic's taste; the next may not share it), not the verdict history.
8. **Confirm a win.** When the critic picks ours, swap A and B - the opposite order, not a new coin flip - and spawn a second fresh critic on a different model from the first, as strong as the harness offers, and not the builder's model where it offers three. The piece has won only when both pick ours. A second coin flip repeats the first order half the time, and a same-model second critic shares the first one's taste for its own kind of output.

## Critic prompt

Use this, verbatim in substance, for every verdict.

```text
Here are A and B and the bar: [critic's copy of the bar sentence]. Open or run both yourself: [inspection steps for this domain]. Under EVIDENCE, write what you see in each, with the path, command output, screenshot or quoted line it came from. Length and feature count are not criteria. Then:
WINNER: A or B. No ties.
GAP: the one biggest thing the loser lacks that the winner has, with what you opened to see it.
FLOOR: [reading floors for this domain] on each, pass or fail, with the output.
```

Fill the inspection steps from the domain file's "What the critic physically does" - only the sentences saying what to run, open or try on each side, never its pair-preparation sentences, which name ours, the reference and the builder. For a domain with no file, write one sentence naming what to run or open on each side. Add nothing else: no checklist, rubric or scale, nothing about the builder, the history, or which side is ours. The critic cannot say "the bar does X" because it does not know which side that is; it says "A has X, B lacks X", and you translate.

Why each rule is there:

| Rule | LLM failure it removes |
| --- | --- |
| Fresh context, no builder notes, no history | The critic anchors on the builder's justification and agrees; a reused critic conforms to its own last answer and, having seen which side changed, knows which side is ours |
| The lead fetches; the critic never hears the reference's name | A critic that knows which side is the reference judges the name, not the work |
| Coin-flip labels; confirming critic with the order swapped | Pairwise judges favour a position, and a swap can flip the verdict; one lucky order looks like a win |
| Confirming critic on a different model | A judge favours text that reads like its own model's output, label or no label; against a human-made reference that is a thumb on ours, and two same-model critics agree for the same reason |
| Wins confirmed, losses not | A false win ends the loop early; a false loss costs one round |
| Observations before the pick | The model decides first and writes observations that fit the decision |
| Length matched by selection, length excluded | Judges prefer the longer or busier candidate, and a builder in a loop learns to pad |
| Binary pick, one gap | Absolute scores are noisier than a pairwise pick and drift across rounds; ten gaps get ten shallow fixes |
| Gap as an observation, not a fix | Two critics prescribe two different fixes for the same shortfall; a builder given fixes chases critic taste instead of the bar |
| Floors run by command before the critic | A builder can win the A/B by breaking something the A/B does not look at |
| Cited evidence, one rerun per round | Critics narrate inspections they did not perform |

## Builder rules

- One worktree per piece for code; its builder and its critic both work from that worktree, never from main. Merge only after the piece's win is confirmed, then rebase the others. For prose, one file per piece; assemble at the whole gate.
- The builder keeps its context while the gap keeps changing: route the next GAP to the same agent by its id with SendMessage, which resumes it with its whole context; record the id in the workbench so it survives compaction. Continuity helps until it does not.
- **A repeated gap escalates, in this order.** Split the piece on that gap. Then retire the builder and spawn a fresh one given only the artifact, the bar sentence, the reference and the last GAP and FLOOR. Then variants: three fresh builders at once, each in its own worktree, each handed a different one-line approach by you so they cannot converge; the critic gets all three and the reference under shuffled labels, picks one and names the runner-up; keep the worktree of the best of ours and continue the piece from it. Log every escalation. A repeated gap never lowers the bar and never ends the loop.
- The builder may study the frozen reference. It may not reproduce it: verbatim reuse of the reference's text, assets or code is a floor failure.

## Parallelism

- Independent pieces are independent loops. Run them concurrently, inside the subagent cap.
- Pieces that share a file or one reader experience are serialised, or the smoother reconciles them at the gate.
- One critic per piece per verdict. A critic handed five pieces averages them.
- Builders and first critics on the strongest model the harness offers: a weaker builder costs a round, and a round costs a critic. The smoother is where a faster model saves money; the confirming critic is the last check against a false win and gets a model as strong as the first.

## Stopping

The exit is winning: every piece confirmed by two critics, then the assembled whole confirmed the same way. There is no round count and no "no improvement, stop".

- A repeated gap escalates; see builder rules.
- A budget exists only if the user named one. When it runs out, stop and report exactly what is still below the bar.
- The user can stop the run at any point (`/goal clear`, or Esc on a loop). The workbench must always read as a complete report.
- Under `/goal` you cannot end the run yourself. When you must stop - budget spent, fetch failed - write the report, then answer each restart with its one-line summary and no tool call; after a few such turns the harness hands control back to the user with the goal still set.

## Waves and the assembled-whole gate

Pieces judged separately drift apart, and a page made of winning pieces can still lose as a page.

A wave is the set of pieces running at once; a run with more pieces than the cap, or with pieces that build on earlier ones, has several. When every piece of a wave is confirmed and another wave follows, smooth what is assembled so far before it starts: one fresh agent harmonises naming, tone, spacing, error handling and the seams, touching as little as harmonising needs; re-run the command floors; every piece it touched gets one fresh critic with the order swapped from its last verdict - it has won twice already, this checks that it still does - and a loss reopens it. A seam found now is cheaper than the same seam at the gate.

When every piece has a confirmed win:

1. **Smooth.** The same pass over the whole; floors re-run after it.
2. **Judge the whole.** The same verdict procedure, the whole of ours against the whole of the reference, confirmed by a second critic like any win. A loss becomes a new piece - usually "coherence" - and the gate runs again.

The run ends when the whole wins or the user stops it; a harder bar is a new run, never a raise mid-run.

## Workbench

The progress page the prompt asks for. One file, rewritten after every verdict, readable by the user without interrupting the run. It is also your state: after compaction, a resumed session or any turn the harness starts on its own, read it first and continue from it. Never re-split and never re-fetch. A question to the user goes unanswered in an unattended run: write it under open questions, proceed on your best assumption, and say which assumption.

```markdown
# <goal> - gauntlet workbench
Bar: <full bar sentence, verbatim>
Critic's bar: <bar sentence with the reference's name removed>
Reference: reference/ - <URL, date, viewport or commit>
Budget: <only if the user set one>

| Piece | Round | Winner | Confirmed | Gap | Floor | Artifact | Builder id | A/B map | Verdicts |
|---|---|---|---|---|---|---|---|---|---|
| hero | 3 | ours | yes (2/2) | - | LH 93 | wt/hero | a1f3 | A=ref B=ours | verdicts/hero-r3-1.md, -2.md |
| motion | 4 | ref | - | no scroll response | LH 91 | wt/motion | 7c02 | A=ours B=ref | verdicts/motion-r4-1.md |
| perf | 2 | - | - | - | FAIL LH 71 (1.8MB hero video) | wt/perf | 9b44 | - | - |

## Gaps named so far
- motion: R1 static hero -> R2 no parallax -> R3 no scroll response -> R4 no scroll response (repeat: split)

## Escalations
- motion R4: split into scroll-response / hover-response

## Open questions for the user
- (none)
```

For visual work, publish it as an Artifact redeployed to the same path after every verdict; an open tab updates in place. The page cannot load files from disk, so a script inlines the current round's screenshots as data URIs - never pass base64 through your own output - and the whole page stays under 16 MiB.

## Report

When the run ends, for any reason: the final artifact, the full bar sentence, the reference manifest, the gap log per piece, the two confirming verdict files per piece, the whole-gate verdicts, what is still below the bar and why, and the budget spent if there was one.

## Dispatch prompts

### BUILDER

```text
You are building [piece] toward [goal]. The bar is [full bar sentence]. The reference is at [path; held-out material excluded]; study it, reuse none of its text, assets or code. [If revising:] GAP: [gap]. FLOOR: [floor result]. Produce the real artifact - working code, a rendered page, a full draft, a runnable query - not a plan. Work in [worktree or file]. Leave no comments, filenames, commit messages or notes that mention rounds, a critic, a bar, or what changed. Do not touch [tests / eval set]. Return one line: the artifact path.
```

### CRITIC

the critic prompt above, with the critic's copy of the bar sentence, the inspection steps and the reading floors filled in. Nothing else.

### VARIANT BUILDERS (escalation)

the builder prompt, plus one line each: "Approach: [one distinct approach chosen by you]."

### SMOOTHER

```text
You are seeing the assembled [goal] for the first time. Pieces were improved separately. Harmonise naming, tone, spacing, error handling and the seams between them, touching as little as that needs. Do not redesign, do not add. Leave no note of what you changed inside the artifact. Return two lines: the artifact path, and the pieces you touched.
```

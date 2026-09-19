# A run, turn by turn

One coding run from paste to pull request, told through the controller's own output. Every status line below is what `gauntletctl status` printed; the event stream behind it is kept with the skill's tests (220 events), and a test folds it through the machine and compares these lines, so this page cannot drift from the code. Read it on a first run or an empty workbench only.

## What the user pasted

```text
/goal Ours beats the bar blind: two fresh critics in a row, the second with A and B swapped on a different model, pick ours on every piece and on the assembled whole, or 150 invocations or 24 hours are spent. Until then, run a gauntlet loop:

Build a TypeScript duration library: parse strings like "2h 30m" to milliseconds and format back, short and long form.

The bar is vercel/ms at its latest tag. Clone it and freeze the copy; judge against the copy, never a description. It must parse 1e6 strings in under 500 ms. Never add a runtime dependency. Write the required tests and a held-out set before any builder starts; no builder edits them.

Split it into the coarsest pieces that can be judged alone; each gets a builder and a fresh critic every round. Only you fetch the bar. The critic gets ours and the bar as A and B in random order and hears the goal, never the bar's name, which is which, or who made either. It opens both, writes what it sees in each, picks one and names the biggest thing the loser lacks. No ties; a hedge is a loss. The builder closes that gap; repeat.

If the same gap comes back, split that piece, then change builders, then fan out variants; never mark it done. When every piece wins, judge the whole the same way.

Update a progress page after every verdict: piece, round, winner, gap. End every turn with pieces confirmed and what is spent. Questions go there, not to me. Only I end this earlier.

Fan out subagents.
```

Under it, write mode's one line: paste it as is, with the effort setting the harness file names, in auto mode or with the skill's allowlist; the hooks enforce the rules only because they were checked in before the run.

## Turn 1 - round zero

The lead reads `running-the-loop.md`, `domains/coding.md` and the harness file, then:

```text
$ gauntletctl init --invocations 150 --hours 24 --goal "a duration library for TypeScript" --bar "..." --critic-bar "..." --invariant "never add a runtime dependency"
$ gauntletctl freeze https://github.com/vercel/ms reference/ms --ref 2.1.3
{"source": "https://github.com/vercel/ms", "ref": "2.1.3", "commit": "...", "removed": [".github/workflows/", ".husky/"], "executed": "nothing", ...}
$ gauntletctl freeze-verify reference/ms --cmd "npm ci" --cmd "npm test"
exit 0  npm ci
exit 0  npm test
$ gauntletctl event SPLIT_DECIDED pieces=3
```

`init` detected Tier 2 (the manifest verifies, the hooks were checked in) and an active sandbox in strict mode with a network allowlist and credential denies, so `freeze-verify` ran; without it, it would have refused and the pieces that need the reference to execute would have been `BLOCKED`. The allowlist in force is the shipped one, `permissions/allowlist.json`: git, the controller, the build, test and render commands; reads of `.gauntlet/private/`, the state file, the log and every env file denied.

The split is coarse: `parse` (string to milliseconds) and `format` (milliseconds to string, short and long), each with a matching part of the reference, plus `locale` (long form in the user's language), which has no counterpart in `ms` and runs champion-challenger beside the nearest real thing, the reference's long form. The floors are beyond 60 lines, so an `author` writes them from the lead's brief:

```text
$ gauntletctl floor add required --cmd "node --test tests/required/"
$ gauntletctl floor add heldout --cmd "node --test heldout/" --derived
$ gauntletctl floor add hostile --cmd "node heldout/hostile.mjs" --derived
$ gauntletctl floor add bench --cmd "node bench/parse.mjs --max-ms 500"
$ gauntletctl floor add no-deps --cmd "node bench/no-deps.mjs" --derived
$ gauntletctl piece open parse --referent reference/ms/parse
$ gauntletctl piece open format --referent reference/ms/format
$ gauntletctl piece open locale --referent reference/ms/format --champion-challenger
$ gauntletctl pair parse --prepare --reference reference/ms/parse --prompt .gauntlet/staging/parse.md --adapter run.mjs
$ gauntletctl commit --plan
```

The user asked for the ported suite and the benchmark number; the held-out set, the hostile script and the dependency check are the lead's, so they are DERIVED, and the invariant "never add a runtime dependency" became the `no-deps` floor because a command can check it. `commit --plan` commits the manifest, the log, the workbench and its copy `plan.md` before any builder exists; this run is unattended, so the DERIVED floors go under open questions and the lead proceeds. Three `editor` builders are dispatched, each with the matched part of the reference, not the tree.

```text
confirmed 0/3 pieces, whole: no | parked: 0 | blocked: 0 | spent: 4/150 inv, 0.3/24 h | tier: 2 | policy v1
```

## Turn 2 - a red floor, and an execution failure

`a1f3` returns `.gauntlet/wt/parse` with its required suite green; the stop hook attests `BUILDER_DONE`. The lead runs what the builder must not see:

```text
$ gauntletctl floors parse
FLOOR_FAIL heldout  .gauntlet/floors/parse/r1
$ gauntletctl event GAP_ROUTED piece=parse class=artifact gap="FLOOR held-out 9/12"
```

No critic: the round is already lost. `a1f3` is resumed with the raw output as FLOOR, nothing else. Meanwhile the locale floor cannot run here at all, which is nobody's artifact: `gauntletctl event BLOCK_REQUESTED piece=locale reason="the locale floor needs full ICU data and this Node build has none"` (class `execution`).

```text
confirmed 0/3 pieces, whole: no | parked: 0 | blocked: 1 | spent: 5/150 inv, 0.6/24 h | tier: 2 | policy v1
```

## Turn 3 - a loss, and a finding that becomes a floor

`7c02` returns `format`; floors green; one command builds the pair and one `reader` gets its path and nothing else:

```text
$ gauntletctl pair format
/work/durations/.gauntlet/pairs/format
dispatch a reader with that path and nothing else
```

The pair holds `a/`, `b/`, `PROMPT.md`, `PAIR_ID`, the adapter, and each side's floor outputs as files; which side is ours is in private storage, where not even the lead can read it. The verdict comes back through the stop hook, is checked for shape and filed as `.gauntlet/verdicts/format-r1-1.md`:

```text
PAIR: format-r1-e360
EVIDENCE:
- A: `node run.mjs a format 5400000` -> 2h; with --long -> 2 hours
- B: `node run.mjs b format 5400000` -> 1.5h; b/format.ts:31 `const v = ms / unit; return trim(v.toFixed(1))`
- A and B: `format("x")` -> both throw; A names the input, B says `expected a number`
WINNER: A
GAP: B prints fractional units (1.5h, 1.5 hours) in an output that is whole-unit everywhere else; seen by running format on 5400000 on each side.
FLOOR: each thrown error names the bad input - A: pass / B: fail
```

The controller translates `A` through the mapping: `CRITIC_LOSS`, class `artifact`. A command could have caught fractional units, so the finding becomes a held-out test in the same round: an `author` stages it and `gauntletctl floor add heldout-whole-units --cmd "node --test heldout/whole-units.test.mjs" --derived --piece format --from .gauntlet/staging/whole-units.test.mjs --to heldout/whole-units.test.mjs` puts it in place. `event GAP_ROUTED piece=format class=artifact`; `7c02` gets GAP and FLOOR, not the observations. ICU data is installed: `event BLOCKER_CLEARED piece=locale note="full-icu installed"`.

```text
confirmed 0/3 pieces, whole: no | parked: 0 | blocked: 0 | spent: 8/150 inv, 1.1/24 h | tier: 2 | policy v1
```

## Turn 4 - a discarded verdict, a resumed builder

`a1f3`, the same agent resumed with its context, returns `parse` round 2; floors green, `pair parse`, a reader. Its verdict puts WINNER before EVIDENCE: the controller records `VERDICT_INVALID` (class `evaluation`), nobody argues with it, and `pair parse` again opens a new attempt on the same pair, because a retry cannot change the experiment. `locale`'s first attempt has green floors, so it is the champion, unjudged.

```text
confirmed 0/3 pieces, whole: no | parked: 0 | blocked: 0 | spent: 10/150 inv, 1.8/24 h | tier: 2 | policy v1
```

## Turn 5 - a confirmed win, and a NOT REPRODUCED the lead accepts

`parse`: the fresh reader picks ours. The lead reruns one cited command (`gauntletctl rerun parse "node run.mjs b parse 1.5.5h"`; wins only), then:

```text
$ gauntletctl swap parse
/work/durations/.gauntlet/pairs/parse
dispatch a reader-alt with that path and nothing else
```

The same files with the labels inverted, a different model: it picks ours. `CONFIRMATION_WIN`; `parse` is `CONFIRMED`. `format` round 2 loses on "B returns undefined for `1.5.5h` instead of throwing"; routed, and `7c02` answers with its one alternative line, `NOT REPRODUCED: node run.mjs b format 1.5.5h -> throws invalid duration: "1.5.5h"`. The lead runs it: `gauntletctl rerun format "node run.mjs b format 1.5.5h"` prints `exit 1  seq 66`, and the output agrees with the builder's, so `gauntletctl event NOT_REPRODUCED_ACCEPTED piece=format rerun=66`. The verdict is discarded (`evaluation`), no gap is routed, and `pair format` spawns a fresh critic.

```text
confirmed 1/3 pieces, whole: no | parked: 0 | blocked: 0 | spent: 14/150 inv, 2.5/24 h | tier: 2 | policy v1
```

## Turn 6 - a lost confirmation, a repeated gap, a split; a challenger becomes champion

`format` wins its first critic and loses the confirmation: "B's long form says `2 hour`; A pluralises". A loss is a loss; routed. Round 3 loses on "long form prints `1 days`": the long-form gap again, so `gauntletctl event GAP_SAME_AS_LAST piece=format`, the controller derives `GAP_REPEATED`, and `next` names the rung:

```text
judgment    ladder, split: decide where; gauntletctl piece split format <child> <child>  [format]
$ gauntletctl piece split format format-short format-long
```

The children share what `format` had left of its allocation and get fresh builders. `locale`'s second attempt beats the champion, is confirmed by the other reader, and becomes the champion (`CHAMPION_REPLACED`); the piece goes on.

```text
confirmed 1/4 pieces, whole: no | parked: 0 | blocked: 0 | spent: 23/150 inv, 3.8/24 h | tier: 2 | policy v1
```

## Turn 7 - after compaction; a parked piece

Context was compacted. The turn opens with `gauntletctl status --full`, not with memory: states, rounds, builder ids and what is legal next all come from the log; nothing is re-split or re-fetched.

```text
confirmed 1/4 pieces, whole: no | parked: 0 | blocked: 0 | spent: 23/150 inv, 3.8/24 h | tier: 2 | policy v1
```

`format-short` wins and is confirmed in one round. `format-long`'s builder tries to install a pluralisation package; the boundary hook denies it and says what to return, and it returns `BLOCKED: pluralisation wants the intl-pluralrules package; installs are outside my directory's rules`. The controller parks the piece (`execution`) and the run goes on. `locale`'s next two challengers both lose to the champion.

```text
confirmed 2/3 pieces, whole: no | parked: 1 | blocked: 0 | spent: 29/150 inv, 5.0/24 h | tier: 2 | policy v1
```

## Turn 8 - a human resumes; a piece converges

The user reads the workbench, where the parked piece is listed first, and runs `gauntletctl resume format-long --actor leo` with a note: Node 22 ships `Intl.PluralRules`. The piece wins and is confirmed. `locale` has lost twice in a row, so the gap-only check runs: `gauntletctl pair locale --gap-only` and a `reader` (`GAP: none`), then `gauntletctl swap locale` and a `reader-alt` on the inverted pair (`GAP: none`). Two readers on two models: `CONVERGED`. The report will say "converged against reference/ms/format", never "beat the bar".

```text
confirmed 4/4 pieces, whole: no | parked: 0 | blocked: 0 | spent: 34/150 inv, 5.9/24 h | tier: 2 | policy v1
```

## Turn 9 - the wave, and the gate lost

The two format pieces share a file, a recorded fact (`event SHARED_EDGE_RECORDED pieces=format-short,format-long`), so one `editor-fast` smooths the merge; `gauntletctl wave parse format-short format-long locale --merge 3f9c2ab` reruns the floors on it: green, four pieces `INTEGRATED`. Then the gate, exactly as a piece, paid from the gate reserve: `piece open whole --kind whole --referent reference/ms`, floors, `pair whole`, a reader. It picks the reference: "B documents parse and format as two imports; A is one function that does both". That is an `artifact` failure with an owner: `piece open coherence --kind coherence`. The same verdict shows something no builder can fix, and that is filed as `scope`, never as a piece:

```text
$ gauntletctl event SCOPE_FAILURE_FILED note="The goal said 'format milliseconds back, short and long form'. The whole gate showed the long form's language is unspecified: ours follows the system locale, the reference is English only. The goal should have said which locales the long form must support, or that English alone is the bar."
```

```text
confirmed 4/5 pieces, whole: no | parked: 0 | blocked: 0 | spent: 38/150 inv, 6.5/24 h | tier: 2 | policy v1
```

## Turn 10 - the whole wins

`coherence` (one entry point, the README rewritten) wins and is confirmed in a round. The gate again: the smoother's pass is a new round, floors green, `pair whole`, a reader, `swap whole`, a reader-alt. The turn ends with the gate's evidence, pasted, above the status line:

```text
$ gauntletctl gate
.gauntlet/verdicts/whole-r2-1.md: WINNER: B
.gauntlet/verdicts/whole-r2-2.md: WINNER: A
confirmed 5/5 pieces, whole: yes (2/2) | parked: 0 | blocked: 0 | spent: 43/150 inv, 7.5/24 h | ended: win
```

B, then A: the same side under inverted labels. The harness's evaluator reads evidence, not a claim.

## Turn 11 - report, commit, promote

```text
$ gauntletctl report --notes .gauntlet/staging/notes.md
$ gauntletctl commit
reference/ms/MANIFEST
.gauntlet/events.jsonl
.gauntlet/workbench.md
.gauntlet/plan.md
.gauntlet/verdicts
.gauntlet/report.md
$ gauntletctl promote
https://github.com/example/durations/pull/12
a human approves it; status reads the merge from the remote
```

`commit` scanned the set for secrets first and staged nothing else: no private storage, no pairs, no reference bytes. The pull request's description, written by `promote`:

```text
Gauntlet run g-20260918-d41c07: a duration library for TypeScript

Bar: A TypeScript duration library that parses and formats like vercel/ms 2.1.3 and beats it on a blind read; floor: ...

confirmed 5/5 pieces, whole: yes (2/2) | parked: 0 | blocked: 0 | spent: 43/150 inv, 7.5/24 h | ended: win

Enforcement: tier 2, attestation tier-1. Compliance pass: check this diff against the bar sentence and the two whole-gate verdicts.

- Reference manifest: reference/ms/MANIFEST
- Plan: .gauntlet/plan.md
- Workbench: .gauntlet/workbench.md
- Report: .gauntlet/report.md
- Event log: .gauntlet/events.jsonl
- Whole-gate verdicts: .gauntlet/verdicts/whole-r2-1.md, .gauntlet/verdicts/whole-r2-2.md

Human resumes: format-long resumed by leo
```

```text
confirmed 5/5 pieces, whole: yes (2/2) | parked: 0 | blocked: 0 | spent: 43/150 inv, 7.5/24 h | ended: win
```

No run merges its own result. A human approved the pull request under branch protection; a later `status` read the merge from the remote and recorded `PR_MERGED`, and only then were the pieces `PROMOTED`:

```text
confirmed 5/5 pieces, whole: yes (2/2) | parked: 0 | blocked: 0 | spent: 43/150 inv, 9.1/24 h | ended: win
```

## The report's metrics

From `gauntletctl metrics`, computed from the log; nothing in the run acted on them.

```text
rounds per confirmed piece                       2.4
red floor share                                  0.05
confirmation flip rate                           0.14
discarded verdict rate                           0.09
not reproduced accepted rate                     0.04
parked pieces                                    1
escalations per piece                            {'gap': 0.17, 'spend': 0.0}
share of escalations from spend                  0.0
invocations per confirmed piece                  8.6
lead turns per confirmed piece                   2.6
controller operations per confirmed piece        40.8
worker minutes per confirmed piece               58.8
tokens per confirmed piece                       214000.0
spend                                            {'local': '38/90', 'escalation': '0/37', 'gate': '5/23'}
unused reserve                                   {'escalation': 37, 'gate': 18}
ended                                            win
ceiling hit                                      False
by class                                         {'artifact': 8, 'evaluation': 2, 'execution': 2, 'scope': 1}
attestation conflicts                            0
fresh builder gap closed within two rounds       -
rounds per confirmed piece after split           1.0
variant escalations whose winner confirmed       -
converged pieces                                 1
converged pieces reopened                        0
whole gate loss rate                             0.33
coherence pieces                                 1
rounds to confirm coherence                      [1]
```

The gap log, one class per entry: eight `artifact` (one red floor, six lost verdicts, one lost gate), two `evaluation` (the verdict with WINNER first; the accepted NOT REPRODUCED), two `execution` (the missing ICU data; the blocked install), one `scope` (the intent draft above). The report lists the resumed piece and the human who resumed it, the whole-gate reserve ended with 18 of 23 unused, and the envelope was never close: 43 of 150 invocations, 7.5 of 24 hours.

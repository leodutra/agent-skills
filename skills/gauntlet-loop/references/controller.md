# The controller, on one page

`gauntletctl` keeps the run's state and says what is legally next. The event log is the truth: state is the fold of `.gauntlet/events.jsonl`, and the workbench is regenerated from it. Exit codes: 0 done, 2 rejected, 3 refused precondition.

## States and moves

Anything not in this table is rejected before it reaches the log.

| From | Event | To | Needs |
| --- | --- | --- | --- |
| (none) | `PIECE_OPENED` | `ACTIVE` | a referent; `REFERENCE_FROZEN` exists; the split recorded |
| `ACTIVE` | `BUILDER_DONE`, `FLOOR_PASS`, `FLOOR_FAIL`, `CRITIC_LOSS`, `VERDICT_INVALID`, `GAP_ROUTED` | `ACTIVE` | a class on every non-win |
| `ACTIVE` | `CRITIC_DISPATCHED` | `ACTIVE` | `FLOOR_PASS` this round: a red floor ends the round |
| `ACTIVE` | `CRITIC_WIN` | `AWAITING_CONFIRMATION` | the verdict file; the pair id |
| `AWAITING_CONFIRMATION` | `CONFIRMATION_WIN` | `CONFIRMED` | attested from `reader-alt`; a different model |
| `AWAITING_CONFIRMATION` | `CONFIRMATION_LOSS` | `ACTIVE` | the verdict file; the gap |
| `AWAITING_CONFIRMATION` | `VERDICT_INVALID` | stays | a fresh `reader-alt` on the same pair |
| `ACTIVE` | `GAP_REPEATED`, `ALLOCATION_SPENT` | `ACTIVE` | the ladder climbs one rung |
| `CONFIRMED` | `WAVE_COMPLETE` | `INTEGRATED` | floors green on the merge; the merge commit |
| `CONFIRMED`, `INTEGRATED` | `FLOOR_FAIL` | `ACTIVE` | a merge, or an amended floor, went red |
| `INTEGRATED` | `RECHECK_LOSS` | `ACTIVE` | the verdict file |
| `INTEGRATED` | `PR_MERGED` | `PROMOTED` | read from the remote by `status`, never from you |
| `ACTIVE`, `AWAITING_CONFIRMATION` | `PIECE_BLOCKED`, `LEASE_EXPIRED` | `BLOCKED` | the reason; class `execution` |
| `BLOCKED` | `BLOCKER_CLEARED` | `ACTIVE` | a note |
| `ACTIVE`, `BLOCKED`, `AWAITING_CONFIRMATION` | `PIECE_PARKED` | `PARKED` | last verdict; the builder's account |
| `PARKED` | `HUMAN_RESUMED` | `ACTIVE` | a named human |
| any but `PARKED` | `ATTEST_CONFLICT` | `ACTIVE` | everything the piece did since the first attestation leaves the fold |

Champion-challenger: a confirmed challenger derives `CHAMPION_REPLACED` and the piece returns to `ACTIVE`; a challenger's loss counts one; after two in a row, `pair --gap-only` yields `GAP_ONLY_RESULT`. A named gap reopens the piece; `GAP: none` from `reader`, then from `reader-alt` on the swapped pair, derives `CONVERGED` to `CONFIRMED`. It is the only `CONFIRMED` without a `CONFIRMATION_WIN`, and needs the same two readers.

## Events

**Judgment**, the only names `event <NAME> k=v...` accepts: `SPLIT_DECIDED` (pieces), `REFERENT_SELECTED`, `MODE_SELECTED`, `VARIANT_APPROACHES_SELECTED` (piece, approaches `a|b`), `GAP_SAME_AS_LAST` (piece), `GAP_ROUTED` (piece, class), `NOT_REPRODUCED_ACCEPTED` (piece, rerun: the seq of a `RERUN_OBSERVED`), `PARK_REQUESTED` (piece, reason, class), `BLOCK_REQUESTED` (piece, reason), `BLOCKER_CLEARED` (piece, note), `SHARED_EDGE_RECORDED` (pieces), `SCOPE_FAILURE_FILED` (note). Classes: `artifact`, `evaluation`, `execution`, `scope`.

**Fact**, produced only by what observed it: `init` (`RUN_STARTED`), `freeze`, `freeze-verify`, `piece` (`PIECE_OPENED`), `floor` (`FLOOR_ADDED`, `FLOOR_AMENDED`), `floors`, `rerun`, `pair` and `swap` (`CRITIC_DISPATCHED`), `wave`, `commit`, `promote`, `status` (`LEAD_TURN`, `LEASE_EXPIRED`, `PR_MERGED`), `resume`, the hooks (`BLIND_BLOCK`, `BOUNDARY_BLOCK`), and `attest`, which only the harness's start and stop hooks invoke (`AGENT_REGISTERED`, `BUILDER_DONE`, `SMOOTHER_DONE`, `CRITIC_RESULT`, `ATTEST_CONFLICT`). **Derived** by the rules: the win, loss and `VERDICT_INVALID` events from `CRITIC_RESULT` and the mapping, `GAP_REPEATED`, `ALLOCATION_SPENT`, `PIECE_PARKED`, `PIECE_BLOCKED`, `CHAMPION_REPLACED`, `CONVERGED`, `RECHECK_LOSS`, `BUDGET_EXHAUSTED`, `RUN_ENDED`.

A verdict stands only when the stop hook delivered it for a registered, not yet attested agent of the type the attempt expects, naming the open attempt's pair, in shape, with a citation. A hedge is a loss. The model recorded is the definition's pin.

## Budgets

The envelope is `E` invocations and `T` hours on one clock, from the prompt's first line or, unnamed, from the piece count. `SPLIT_DECIDED` apportions it: local 60%, escalation 25%, gate 15% (bootstrap). Each piece gets local divided by pieces; a split shares the parent's remainder. One debit per spawn, on the event that opens the attempt. A piece pays local, then escalation; the whole pays the gate reserve, and no piece can reach it. A spent allocation derives `ALLOCATION_SPENT`. With allocation and reserve both gone, the next spawn is refused and the piece parks. `E` or `T` reached derives `BUDGET_EXHAUSTED`. The run ends on `win`, `nothing-left` (every remaining piece parked) or `ceiling`; afterwards no work event is accepted.

## Escalation

`GAP_REPEATED` (from your `GAP_SAME_AS_LAST`) and `ALLOCATION_SPENT` climb the same ladder: split (`piece split`), fresh builder, variants (two approaches first, a third only if both lose; each judged as an ordinary pair; if all lose, `pair --pick` says which continues; one variant escalation at a time across the run), then `PIECE_PARKED`. It never lowers the bar and never ends the run.

## Authorities

| Who | May | May not |
| --- | --- | --- |
| You, the lead | judge: split, referent, mode, approaches, same-gap calls, park and block requests; dispatch; route gaps | submit a fact; edit state; change the policy; merge |
| The controller | transition, account, build pairs, run floors, attest, translate verdicts, render the workbench, compute metrics | make a judgment call; change what a win is |
| A script | establish a fact: pass or fail, a number | grade |
| A human | change the bar (a new run), change scope, resume a parked piece, approve the pull request, change the policy version | be asked mid-run by a hook |

`policy/v1.json` is pinned at `init` and a changed version is refused mid-run. It names which two models confirm, never whether.

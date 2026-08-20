# Backlog — Claude Code Context Stack

Open work items, one per defect. **This file carries no rationale** — every "why"
belongs in [`DECISIONS.md`](DECISIONS.md) (D36, D45). An item here states what is
wrong, the evidence, and what "done" looks like; nothing more.

**This file empties itself.** Closing an item means appending a decision (the
next free `D<n>` — IDs are permanent, so claim one only when it lands), adding a
[`CHANGELOG.md`](CHANGELOG.md) line, and deleting the item from here. An item
that has been sitting unclosed long enough to feel permanent is a decision to
*decline* the work — write that decision (D37 and D39 are the model) and delete
the item.

Ordered by cost. `Touches` names the decisions an item would amend; per the
append-only rule those bodies are never edited, only given a status line.

---

## B7 — Evaluate the Serena retention gate

**Touches:** [D53](DECISIONS.md#d53), [D57](DECISIONS.md#d57)

Serena has never executed a tool on the reference machine (40 spawns, 0 calls,
0 memories). [D57](DECISIONS.md#d57) retains it on the grounds that the install
was never completed, so the question was never fairly put.

**Evidence:** `stack-init verify` reports the count; the raw check is
`grep -rl 'activate_project: .*session_id:' ~/.serena/logs/ | wc -l`.

**Done looks like:** after ~10 real sessions following a completed
`stack-init global`, the count is read. Non-zero -> append a decision closing
the gate and delete this item. Zero -> append a decision removing Serena *and*
`stack-init`, since installing one plugin does not need an installer.

---

## No other open items

B1–B6 closed in 2.4 as D39–D44. Four were closed by deciding rather than
building — two gates that could never fire (D39, D40), one circular standing
check restated as a readable number (D41), and one premise correction that
brought back a narrower checker than the one removed (D42). Two were code:
D43 (contract refresh by hook) and D44 (`--no-tokensave` probed at launch).

---

## Not on this list

**D2 (two installers per OS)** has the highest defect count in the log — D27,
D30, D31 and D32 are all repairs of the same two-implementation drift. It needs
no reconsideration: the single-binary consolidation D38 already refers to is the
answer, and it is execution, not a decision. Note that D38's budget argument
holds only while that consolidation is actually moving, and D42 has now added one
deliberate, recorded exception to the equivalence rule (`verify --docs`, Unix
only) rather than a drifting one.

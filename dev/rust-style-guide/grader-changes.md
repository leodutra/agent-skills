# Grader changes

Every change to a grader after a run graded with it. `bench.py --resume/--regrade --grader-change
"<reason>"` appends here and regrades that case in every arm. The four entries before the freeze
existed are backfilled by hand: all four were made after reading failures of the skill's own arm,
and no arm was searched for false passes, so they may lean the scores toward the skill.

- 2026-11-15 rsg-20261114-234541-gocqx7tb: review-orders-store 06 — accept a finite-float refinement whose constructor rejects NaN (the rewrite's own fix); regraded both arms.
- 2026-11-15 rsg-20261114-235302-42fkfrhf: review-cli-format-flag 04 — accept writeln! with its error handled in place of println!; regraded all three arms.
- 2026-11-15 after rsg-20261115-000044-ia3ulb76: review-match-roster 03 — accept making an empty roster unrepresentable at the input; that workspace was not regraded (its gradings were later lost to a --dry-run bug).
- 2026-11-15 rsg-20261115-064514-hqh1zgag: review-route-distances 01 — accept that the serde(transparent) bypass undermines Eq, and a derived PartialEq; regraded both arms.

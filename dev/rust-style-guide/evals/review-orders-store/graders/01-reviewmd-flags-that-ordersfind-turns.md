---
type: llm
focus: trace
weight: 1
---

review.md flags that Orders::find turns a store failure into None (.ok().flatten()), so a failing store reads as a missing order, and asks for Result<Option<Order>, StoreError> (or an equivalent that keeps the failure)

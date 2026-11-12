---
type: llm
focus: trace
weight: 1
---

review.md flags that capture is left half done when its future is dropped (cancelled, timed out) or the call is retried between the charge and the record: the card is charged but the capture is not recorded, or it is charged twice. Its fix keeps the charge and the record from coming apart, by any concrete means: for example an idempotency key sent to the provider, recording the attempt before charging and checking it, or a transaction. Naming the hazard with no fix does not count

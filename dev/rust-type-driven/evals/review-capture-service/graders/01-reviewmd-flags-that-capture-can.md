---
type: llm
focus: trace
weight: 1
---

review.md flags that capture can charge twice when retried or cancelled between the charge and the record, and asks for an idempotency key (or a check before charging) recorded atomically with the result

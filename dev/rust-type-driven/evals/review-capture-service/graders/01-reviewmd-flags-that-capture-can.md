---
type: llm
focus: trace
weight: 1
---

review.md flags that capture can charge twice when retried or cancelled between the charge and the record, and asks for an idempotency key (such as the order id sent to the provider) with a durable record of the capture checked before charging

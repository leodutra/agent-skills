---
type: llm
focus: trace
weight: 1
---

review.md flags both `let _ignored = save_receipt()` and `drop(save_receipt())` as silently discarding store failures, and asks for handling or explicitly justified treatment of the errors.

---
type: llm
focus: trace
weight: 1
---

review.md flags `let _future = async { save_receipt() }` as a future that is never polled and asks to await, return or supervise it.

---
type: llm
kind: correctness
focus: trace
weight: 1
---

review.md flags that post updates self.balance before the write succeeds, so a cancelled or failed write leaves the in-memory balance counting an entry the file doesn't hold; it asks to update the balance only after the write (and sync) completes

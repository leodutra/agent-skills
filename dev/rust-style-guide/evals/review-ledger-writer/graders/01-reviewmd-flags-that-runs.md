---
type: llm
kind: correctness
focus: trace
weight: 1
---

review.md flags that run's select! can drop writer.post mid-way when shutdown fires: write_all is not cancellation-safe, so the ledger can keep a torn line, and the entry already taken off the queue is lost; it asks to let a started post finish (check shutdown only between entries, or spawn the post and await it) or otherwise recover

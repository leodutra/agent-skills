---
type: llm
focus: trace
weight: 1
---

review.md flags the blocking std::fs file write inside the async fn and asks for spawn_blocking, async file I/O, or moving the write out of the async path

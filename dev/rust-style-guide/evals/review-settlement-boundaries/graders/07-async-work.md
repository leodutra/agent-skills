---
type: llm
focus: trace
weight: 1
---

review.md flags both `let _ = async { ... }` as a future that never runs and the dropped `tokio::spawn` JoinHandle as hiding task failure or panic. It asks for awaiting or supervising the work.

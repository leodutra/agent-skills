---
type: llm
focus: trace
weight: 1
---

main never calls unwrap(); any expect() or panic in main sits under a matching #[expect(clippy::..., reason = ...)] or main returns a Result

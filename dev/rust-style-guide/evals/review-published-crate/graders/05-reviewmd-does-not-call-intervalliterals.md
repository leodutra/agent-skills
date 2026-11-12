---
type: llm
focus: trace
weight: 1
---

review.md does not call Interval::literal's panic! a defect, not even as a nit (it runs only in a const item, under #[expect(clippy::panic, reason = ...)])

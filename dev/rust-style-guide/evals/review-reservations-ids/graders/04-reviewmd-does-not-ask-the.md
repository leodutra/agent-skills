---
type: llm
focus: trace
weight: 1
---

review.md does not ask the id newtypes for private fields or a validating constructor (a try_new returning Result): any id is valid, so they are tags with a pub field, and From and #[serde(transparent)] on them are fine

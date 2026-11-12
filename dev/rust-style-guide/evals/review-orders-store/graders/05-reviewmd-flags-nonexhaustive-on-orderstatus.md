---
type: llm
focus: trace
weight: 1
---

review.md flags #[non_exhaustive] on OrderStatus as wrong here (the crate is built with the rest of the workspace and never published, and the attribute forces wildcard arms in the other crates), and asks to remove it

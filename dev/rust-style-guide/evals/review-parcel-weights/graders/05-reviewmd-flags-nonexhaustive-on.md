---
type: llm
focus: trace
weight: 1
---

review.md flags #[non_exhaustive] on Carrier: the crate is built with the rest of the workspace and never published, so the attribute protects no outside user and only forces wildcard arms in the workspace's other crates, which then miss a new carrier silently; it asks to remove it

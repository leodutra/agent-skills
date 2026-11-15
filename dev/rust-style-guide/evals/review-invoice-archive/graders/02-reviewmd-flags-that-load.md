---
type: llm
focus: trace
weight: 1
---

review.md flags that `load`, a domain function, returns serde_json::Error raw, and asks for an error type of its own (for example an ArchiveError variant) that keeps the cause as #[source]

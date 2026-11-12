---
type: llm
focus: trace
weight: 1
---

Errors in the library are typed (thiserror or std::error::Error impls: an enum, or a unit struct for a single failure), not String, &str or anyhow

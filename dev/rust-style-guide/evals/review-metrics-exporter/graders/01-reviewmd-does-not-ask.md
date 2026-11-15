---
type: llm
focus: trace
weight: 1
---

review.md does not ask to remove the public Exporter trait or replace it with a concrete type or an enum of backends, not even as a nit: it is the published crate's extension point for outside implementors, which justifies it with one in-crate implementation

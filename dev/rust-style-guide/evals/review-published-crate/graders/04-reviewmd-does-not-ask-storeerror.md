---
type: llm
focus: trace
weight: 1
---

review.md does not ask StoreError to derive Clone, PartialEq or Eq, not even as a nit (it wraps std::io::Error, which has none of them)

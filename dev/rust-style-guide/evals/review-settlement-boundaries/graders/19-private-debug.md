---
type: llm
focus: trace
weight: 1
---

review.md flags the private `AccountNumber` refinement lacking `Debug`, which the public-only `missing_debug_implementations` lint misses, and asks to derive or implement `Debug`.

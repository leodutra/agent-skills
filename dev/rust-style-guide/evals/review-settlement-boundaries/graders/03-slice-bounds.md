---
type: llm
focus: trace
weight: 1
---

review.md flags `charges[0]` and `&charges[1..3]` as panicking for shorter valid slices, and asks for `get` or an explicit bounds check with a handled failure.

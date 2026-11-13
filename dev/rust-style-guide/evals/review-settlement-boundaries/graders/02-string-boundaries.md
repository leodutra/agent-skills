---
type: llm
focus: trace
weight: 1
---

review.md flags both `&reference[..2]` and `reference.split_at(2)` as capable of panicking on short input or a non-UTF-8 boundary, and proposes a safe split/get or character-aware approach.

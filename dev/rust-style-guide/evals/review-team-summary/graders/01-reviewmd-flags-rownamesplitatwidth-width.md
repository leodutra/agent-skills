---
type: llm
kind: correctness
focus: trace
weight: 1
---

review.md flags `row.name.split_at(width)`: width is used as a byte offset, so a name with a multi-byte character (José, Zoë) panics when the offset lands inside that character; it asks to cut at a character boundary (char_indices, chars().take, or similar)

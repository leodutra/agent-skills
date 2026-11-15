---
type: llm
kind: correctness
focus: trace
weight: 1
---

review.md flags `impl Eq for Fix`: its raw f64 fields can hold NaN, so the hand-written Eq claims a reflexivity f64 does not have; it asks to drop Eq (and change the set-based dedup) or to make the coordinates finite refinements

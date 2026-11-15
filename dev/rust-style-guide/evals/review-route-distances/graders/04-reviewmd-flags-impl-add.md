---
type: llm
kind: correctness
focus: trace
weight: 1
---

review.md flags `impl Add for Kilometres` building Self directly: two finite distances can sum to infinity, breaking the finite invariant; it asks for an addition that keeps the invariant (a checked add returning Result or Option, or a constructor call)

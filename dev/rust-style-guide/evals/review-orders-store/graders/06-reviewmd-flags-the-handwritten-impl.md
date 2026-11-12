---
type: llm
focus: trace
weight: 1
---

review.md flags the hand-written impl Eq for Weight as wrong because Weight wraps an f64, whose NaN is not equal to itself (from_kg accepts NaN), so Eq's reflexivity does not hold; the fix removes it or stores the weight in a type that is Eq, such as integer grams

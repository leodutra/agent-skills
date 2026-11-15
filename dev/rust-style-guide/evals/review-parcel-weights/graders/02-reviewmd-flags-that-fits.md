---
type: llm
kind: correctness
focus: trace
weight: 1
---

review.md flags that `fits` compares the parcel's weight in grams against the carrier's limit in ounces: a live bug (a 1,500 g parcel, about 53 oz, is refused by the courier's 1,120 oz limit)

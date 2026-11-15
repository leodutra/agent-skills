---
type: llm
kind: correctness
focus: trace
weight: 1
---

review.md flags that Kilometres::try_new accepts -0.0, which compares equal to 0.0 under PartialEq but hashes differently (to_bits) and orders differently (total_cmp), and asks to normalize -0.0 to 0.0 in try_new or otherwise make Eq, Hash and Ord agree

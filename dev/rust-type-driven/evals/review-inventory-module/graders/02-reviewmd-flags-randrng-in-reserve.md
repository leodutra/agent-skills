---
type: llm
focus: trace
weight: 1
---

review.md flags rand::rng() in reserve as ambient randomness in domain code, and its fix has the caller pass in the id, a generator or a random source (an internal counter or atomic as the only fix does not count)

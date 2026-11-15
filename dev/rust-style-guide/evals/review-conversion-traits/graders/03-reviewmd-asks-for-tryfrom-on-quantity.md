---
type: llm
kind: convention
focus: trace
weight: 1
---

review.md flags Quantity::from_u32 as a context-free fallible conversion with no TryFrom<u32> and asks for impl TryFrom<u32> for Quantity; keeping from_u32 beside it, or renaming it to try_new, is fine

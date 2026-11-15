---
type: llm
kind: convention
focus: trace
weight: 1
---

review.md does not ask to replace Weight::from_grams(u32) with From/TryFrom<u32>, nor to add a Grams type, not even as a nit: a bare u32 can't say its unit, so the named constructor is right where the raw number enters, and no bare quantity travels further in this module

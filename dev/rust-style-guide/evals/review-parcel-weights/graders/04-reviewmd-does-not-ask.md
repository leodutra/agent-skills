---
type: llm
focus: trace
weight: 1
---

review.md does not ask to replace Parcel::from_grams(u32) with From<u32> or TryFrom<u32>, not even as a nit: the scale's bare u32 can't carry its unit, so a named constructor where the number enters is right (having it take a Grams type instead is fine)

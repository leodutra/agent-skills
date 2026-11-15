---
type: llm
kind: convention
focus: trace
weight: 1
---

review.md does not propose From, Into or TryFrom between grams and ounces, not even as a nit: grams_to_ounces rounds down, so the conversion stays a named function (a named method on a unit type is fine)

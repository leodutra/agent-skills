---
type: llm
focus: trace
weight: 1
---

review.md flags that Sku::new keeps the case it was given although SKUs are case-insensitive (its doc comment says so), while Sku derives PartialEq, Eq and Hash, so ab-12 and AB-12 compare unequal; the fix normalizes the case in the constructor

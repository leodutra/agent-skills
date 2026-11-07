---
type: llm
focus: trace
weight: 1
---

review.md flags #[serde(transparent)] on Iban as building an Iban without its validation, and asks for serde try_from (or equivalent) through the constructor

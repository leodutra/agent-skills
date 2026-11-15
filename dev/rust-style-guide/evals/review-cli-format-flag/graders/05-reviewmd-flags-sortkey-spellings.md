---
type: llm
focus: trace
weight: 1
---

review.md flags that SortKey's FromStr spells Quantity "qty" and rejects "quantity", the serde name stockctl.toml uses, so one value has two different spellings depending on where it is read; it asks for one canonical text (for example clap::ValueEnum or a FromStr that accepts the serde names; an extra alias accepted by both is fine)

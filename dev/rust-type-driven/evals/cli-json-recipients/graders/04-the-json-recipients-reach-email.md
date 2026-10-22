---
type: llm
focus: trace
weight: 1
---

The JSON recipients reach Email only through its validation: #[serde(try_from = ...)] on Email, or a DTO of strings converted with TryFrom/FromStr; Email has no derived Deserialize or #[serde(transparent)]

---
type: llm
focus: trace
weight: 1
---

The JSON recipients reach Email only through its validation: #[serde(try_from = ...)] on Email (which needs the derive), or a DTO of strings converted through Email's validating constructor (new, TryFrom or FromStr); Email has no plain derived Deserialize and no #[serde(transparent)]

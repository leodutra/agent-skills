---
type: llm
focus: trace
weight: 1
---

The JSON recipients deserialize straight into Email through its validation (#[serde(try_from = ...)] on Email, which needs the derive): no struct or DTO holds them as strings to convert later; Email has no plain derived Deserialize and no #[serde(transparent)]

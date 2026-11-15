---
type: llm
kind: convention
focus: trace
weight: 1
---

Deserializing the JSON runs the validation: rules and their fields deserialize through their constructors (#[serde(try_from = ...)] on the types, or a private raw struct whose TryFrom calls them); no type with an invariant has a plain derived Deserialize or #[serde(transparent)], and no validate() method is called after deserializing

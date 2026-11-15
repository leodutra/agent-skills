---
type: llm
focus: trace
weight: 1
---

review.md flags #[serde(transparent)] (the derived Deserialize) on Kilometres: deserializing a Leg from the routing service's JSON skips try_new, so a negative length becomes a Kilometres; it asks for deserialization through the constructor (#[serde(try_from = "f64")] or equivalent). StopId's transparent derive, a tag with no invariant, is fine

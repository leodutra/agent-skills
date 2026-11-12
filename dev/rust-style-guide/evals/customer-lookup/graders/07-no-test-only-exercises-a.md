---
type: llm
focus: trace
weight: 1
---

No test exists only to exercise a derived trait (Clone, Debug output, PartialEq on equal values) or a plain getter. Tests of the Display/FromStr round trip (a property test the skill requires), of accepted and rejected inputs, of case handling and of register/find behavior are not such tests

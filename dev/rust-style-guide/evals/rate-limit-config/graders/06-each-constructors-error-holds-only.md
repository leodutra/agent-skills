---
type: llm
kind: convention
focus: trace
weight: 1
---

Each constructor's error type holds only the failures that constructor can produce: the route, the window and the rule do not share one catch-all error enum (a load error that wraps them, or the JSON error, is fine)

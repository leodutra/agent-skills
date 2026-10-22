---
type: llm
focus: trace
weight: 1
---

Email and the SMTP port are domain types with private fields, each built through one validating constructor; any inherent fallible constructor is named new (not try_new or parse), and a compile-time helper such as const fn literal calls that constructor rather than building Self itself

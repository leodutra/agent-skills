---
type: llm
focus: trace
weight: 1
---

The email type lowercases the domain part in its constructor and keeps the local part exactly as typed, so equality and hashing treat Ann@Example.com and Ann@example.com as one email and ann@example.com as another; a test pins the domain-case equality

---
type: llm
kind: convention
focus: trace
weight: 1
---

review.md flags `count_accounts` taking a `HashMap` by value despite only reading its length, and asks for a borrowed parameter.

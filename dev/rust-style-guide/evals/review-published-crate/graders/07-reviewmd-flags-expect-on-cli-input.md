---
type: llm
focus: trace
weight: 1
---

review.md flags the expect() calls on the command-line argument in main.rs: a missing or mistyped argument is ordinary user input, and expect() turns it into a panic (exit code 101) instead of a usage message and an error exit, and asks to report it as an error

---
type: llm
focus: trace
weight: 1
---

review.md flags that InvalidToken puts the rejected upload token in its message (and its Debug), so the secret reaches logs and panic output, and asks for an error that does not echo the input

---
type: llm
focus: trace
weight: 1
---

review.md flags `require_terminal_line` asserting on terminal input, which can panic on an empty line, and asks for a handled error or parsed input type.

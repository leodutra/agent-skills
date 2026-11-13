---
type: llm
focus: trace
weight: 1
---

review.md flags `Price(pub f64)` as using binary floating point for money, which can round exact amounts, and asks for integer minor units or a decimal representation.

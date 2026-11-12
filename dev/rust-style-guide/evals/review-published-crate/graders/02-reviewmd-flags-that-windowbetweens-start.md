---
type: llm
focus: trace
weight: 1
---

review.md flags that Window::Between's start and end are public variant fields, so a window whose end is not after its start can be built, and asks to move them into a struct with private fields and a validating constructor that the variant wraps (or an equivalent that makes an inverted window unrepresentable)

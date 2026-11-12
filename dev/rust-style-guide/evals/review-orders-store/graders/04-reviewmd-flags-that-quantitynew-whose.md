---
type: llm
focus: trace
weight: 1
---

review.md flags that Quantity::new, whose only failure is zero, returns the shared ValidationError enum, whose other variants it can never produce, and asks for an error holding only that failure (such as a unit struct)

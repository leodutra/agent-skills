---
type: llm
focus: trace
weight: 1
---

review.md flags that on_checkout passes order.id as the customer and order.customer_id as the order (swapped arguments, a live bug), and says distinct id types would make this a compile error

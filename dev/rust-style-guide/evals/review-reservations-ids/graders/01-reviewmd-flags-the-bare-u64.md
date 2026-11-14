---
type: llm
focus: trace
weight: 1
---

review.md flags that reserve takes customer_id, order_id and warehouse_id as bare u64s that a caller can pass in the wrong order, and asks for a distinct newtype per id (such as CustomerId, OrderId, WarehouseId)

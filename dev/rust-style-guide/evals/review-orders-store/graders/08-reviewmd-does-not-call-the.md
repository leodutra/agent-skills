---
type: llm
focus: trace
weight: 1
---

review.md does not call the Result<Option<Order>, StoreError> of LoadOrders::load a defect (for example by asking for a NotFound error variant or a plain Option instead), not even as a nit

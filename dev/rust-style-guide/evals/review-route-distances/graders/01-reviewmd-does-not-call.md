---
type: llm
focus: trace
weight: 1
---

review.md does not call the hand-written `impl Eq for Kilometres` a defect or ask to remove it, not even as a nit: try_new rejects NaN, so the invariant makes equality reflexive (findings about -0.0, Hash or Ord consistency on Kilometres are a different matter and do not fail this)

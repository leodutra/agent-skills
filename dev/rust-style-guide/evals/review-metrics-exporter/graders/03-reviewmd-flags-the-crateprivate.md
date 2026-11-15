---
type: llm
focus: trace
weight: 1
---

review.md flags the crate-private FlushPolicy trait (one implementation, EveryN; no test double; pub(crate), so no outside implementors) as an abstraction nobody needs, and asks to replace it and the Box<dyn FlushPolicy> with the concrete count check (for example a NonZeroUsize field)

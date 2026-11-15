---
type: llm
focus: trace
weight: 1
---

The burst-not-above-limit rule lives in the rule type's own constructor, so no rule with a burst above its limit can be built by any path (not only checked in load, a DTO's TryFrom, or a validate method), and the rule's fields are private

---
type: llm
focus: trace
weight: 1
---

review.md flags render's `_ =>` arm, which renders any string other than json or csv as a table: a silent fallback that an exhaustive match on the enum removes

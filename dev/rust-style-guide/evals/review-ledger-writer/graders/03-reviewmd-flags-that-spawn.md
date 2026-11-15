---
type: llm
kind: correctness
focus: trace
weight: 1
---

review.md flags that spawn drops the JoinHandle of run, so its LedgerError (and any panic) vanishes; it asks for the handle to be returned and awaited, or supervised

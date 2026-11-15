---
type: llm
kind: convention
focus: trace
weight: 1
---

review.md flags Recorder::new returning Option (None when flush_every is 0): a fallible constructor named new that reports failure as absence; it asks to take NonZeroUsize (so it can't fail) or for try_new returning a Result with an error saying why

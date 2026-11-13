---
type: llm
focus: trace
weight: 1
---

review.md flags the bare `#[allow(clippy::cast_possible_truncation)]` as suppressing the lint without a reason or stale-expectation check, and asks to remove it once the cast is fixed, or to replace it with `#[expect(..., reason = "...")]` if a justified exception remains.

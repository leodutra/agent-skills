---
type: llm
focus: trace
weight: 1
---

review.md flags `parse_account` converting a named parse error to `String` with `map_err(|cause| cause.to_string())`, losing the typed source, and asks for a typed error that retains the cause.

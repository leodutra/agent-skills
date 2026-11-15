---
type: llm
kind: convention
focus: trace
weight: 1
---

review.md flags that a_failing_store_fails_the_archive asserts only matches!(…, Err(_)), which also passes for the wrong failure (an Encode error), and asks it to assert the specific variant, such as matches!(result, Err(ArchiveError::Store { .. })) (ArchiveError can't derive PartialEq, so matches! on the variant is the exact form)

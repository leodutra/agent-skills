---
type: llm
kind: convention
focus: trace
weight: 1
---

review.md flags that the two rejection tests don't assert the exact error (matches!(…, Err(_)) and is_err_and(|e| e != Empty) pass for the wrong failure) and asks for assert_eq! on the specific error, such as Err(RosterError::Empty) and Err(RosterError::Duplicate(PlayerId(1)))

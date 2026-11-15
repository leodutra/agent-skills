---
type: llm
kind: convention
focus: trace
weight: 1
---

Every rejection reason (bad route prefix, each limit or window bound, burst above the limit) is reached by a test that asserts its specific error (assert_eq! on the error, or matches! on the exact variant where the error can't be PartialEq), never only is_err()

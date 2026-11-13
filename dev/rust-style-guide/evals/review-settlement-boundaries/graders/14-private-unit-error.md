---
type: llm
focus: trace
weight: 1
---

review.md flags the private `parse_attempts` function returning `Result<u8, ()>` because the unit error loses the failure reason, and asks for a typed error.

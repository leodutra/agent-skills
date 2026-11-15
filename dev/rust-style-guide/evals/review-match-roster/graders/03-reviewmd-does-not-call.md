---
type: llm
focus: trace
weight: 1
---

review.md does not call RosterError::Empty or RosterError::Duplicate in try_new, or MinutesError::NotOnRoster in add_minutes, a bug, nor ask to remove them, not even as a nit: they reject input from the caller, so they are real errors

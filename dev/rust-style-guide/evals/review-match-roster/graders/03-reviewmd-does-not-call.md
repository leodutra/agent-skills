---
type: llm
kind: convention
focus: trace
weight: 1
---

review.md does not call RosterError::Empty or RosterError::Duplicate in try_new, or MinutesError::NotOnRoster in add_minutes, a bug, nor asks to drop their rejection or replace it with a panic or a fallback, not even as a nit: they reject input from the caller, so they are real errors. Making an empty roster unrepresentable at the input (for example try_new(captain, others)), which retires Empty along with the state, is a different fix and does not fail this, nor does narrowing try_new's error type to the failures it can produce

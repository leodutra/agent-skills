---
type: llm
focus: trace
weight: 1
---

review.md flags captain() returning Err(RosterError::NoCaptain) for a state try_new already rules out (an empty roster): a bug dressed as an error variant; it asks to make the state unrepresentable (for example the captain stored apart from the rest, or a non-empty type, so captain() returns &Player) or, where it keeps the check, a reasoned #[expect(clippy::unreachable)], not an error callers must handle

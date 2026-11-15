---
type: llm
kind: convention
focus: trace
weight: 1
---

review.md flags captain_minutes's unwrap_or_default(): every roster player has a minutes entry by construction, so a miss is a bug the default hides as 0 minutes; it asks to make it unrepresentable (for example minutes kept beside each player) or to mark the claim, not to fall back silently

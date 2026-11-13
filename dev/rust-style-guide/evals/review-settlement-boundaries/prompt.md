---
tags: [skill-creator]
max_turns: 40
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Can you review `src/domain/settlement.rs` before I merge it? CI currently runs Clippy's default
lints, not the rust-style-guide lint set. Put the review in review.md: each problem with its line,
why it matters, and the fix. Skip formatting.

Input file: src/domain/settlement.rs

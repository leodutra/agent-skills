---
tags: [skill-creator]
max_turns: 40
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Can you review the route module for the delivery planner, `src/domain/route.rs`, before I merge it? CI runs `cargo clippy --all-targets -- -D warnings` with our lint set and it's green, so skip formatting. Put the review in review.md: each problem with its line, why it matters, and the fix.

Input files: src/domain/route.rs

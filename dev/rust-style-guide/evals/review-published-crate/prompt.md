---
tags: [skill-creator]
max_turns: 40
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

We publish `acme-measure` on crates.io: other teams' services depend on it and implement its `ReadingStore` over their own databases, and it ships a small CLI. Can you review `src/lib.rs` and `src/main.rs` before we release 2.0? CI runs `cargo clippy --all-targets -- -D warnings` with our lint set and it's green, so skip formatting. Put the review in review.md: each problem with its line, why it matters, and the fix.

Input files: src/lib.rs, src/main.rs

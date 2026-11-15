---
tags: [skill-creator]
max_turns: 40
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Can you review the postage module, `src/domain/postage.rs`? It decides which carrier can take a parcel and what it costs. The crate is part of our workspace and isn't published; the counter app and the shipping service are the other crates that use it. CI runs `cargo clippy --all-targets -- -D warnings` with our lint set and it's green, so skip formatting. Put the review in review.md: each problem with its line, why it matters, and the fix.

Input files: src/domain/postage.rs

---
tags: [skill-creator]
max_turns: 40
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Here's the `stockctl export` command, `src/main.rs`; the snapshot loading and the renderers live in our `stock` library, already reviewed. Can you review the CLI side before I merge? CI runs `cargo clippy --all-targets -- -D warnings` with our lint set and it's green, so skip formatting. Put the review in review.md: each problem with its line, why it matters, and the fix.

Input files: src/main.rs

---
tags: [skill-creator]
max_turns: 40
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Can you review the invoice archive before I merge? It's the filesystem blob store, `src/infra/fs_store.rs`, and the domain side that uses it, `src/domain/archive.rs`; `Invoice` and `InvoiceNumber` are in a module that's already reviewed. CI runs `cargo clippy --all-targets -- -D warnings` with our lint set and it's green, so skip formatting. Put the review in review.md: each problem with its line, why it matters, and the fix.

Input files: src/infra/fs_store.rs, src/domain/archive.rs

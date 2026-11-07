---
tags: [skill-creator]
max_turns: 40
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Write a small Rust CLI crate called `notify` (a library plus a binary, using clap derive). `notify send --to <email>` sends to one or more recipients: the flag can repeat and also takes a comma-separated list. `--smtp-port <port>` defaults to 2525 and can never be 0. Recipients can also come from a JSON file, `--recipients-file path.json`, holding `{"recipients": ["a@example.com", ...]}`; an invalid email in the file must be rejected with a clear error, never skipped. For now `send` just prints the validated recipients and port. Add tests, and make sure `cargo clippy --all-targets -- -D warnings` and `cargo test` pass.

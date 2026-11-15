---
tags: [skill-creator]
max_turns: 40
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

I need a small library crate, `limits`, that loads our API rate-limit rules from JSON (an array of rules). Each rule has a route prefix (must start with `/` and contain no whitespace), a request limit per window (at least 1), a window length in seconds (1 to 3600), and an optional burst which, when given, can't exceed the limit. Expose a `load(json: &str)` that returns the rules. Add tests for the invalid cases, and make sure `cargo clippy --all-targets -- -D warnings` and `cargo test` pass.

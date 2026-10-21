---
tags: [skill-creator]
max_turns: 40
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Write a Rust library crate called `orders` that models an order's lifecycle: a draft can be placed; a placed order can be shipped (we need the carrier's tracking number at that point) or cancelled (with a reason); a shipped order can be delivered. Invalid transitions must be errors, not panics. Include unit tests and one integration test under tests/ that walks an order from draft to delivered. `cargo clippy --all-targets -- -D warnings` and `cargo test` must pass.

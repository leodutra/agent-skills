---
tags: [skill-creator]
max_turns: 40
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

I'm building the signup part of our service. Create a cargo library crate called `customers`: `register` takes an email and a display name and stores a new customer, and `find_by_email` looks one up. Storage will be Postgres later, so define the storage interface and give me an in-memory version for the tests. Email lookups must ignore case in the domain part (`Ann@Example.com` and `Ann@example.com` are the same customer) but keep the part before the `@` exactly as typed. Registering an email that is already taken is an error. Add tests, and make sure `cargo clippy --all-targets -- -D warnings` and `cargo test` pass.

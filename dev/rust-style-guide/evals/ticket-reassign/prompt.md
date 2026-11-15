---
tags: [skill-creator]
max_turns: 40
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Add a library crate `tickets` to our workspace (it's built together with our other crates and never published). A ticket has an id, a title, an assignee (a user id) and a status: open, in progress, blocked or closed, and more statuses will come. Statuses are stored as text in the database (`open`, `in-progress`, `blocked`, `closed`) and shown with the same names in our CLI. Define a `TicketStore` interface with `get` and `save` (it will be Postgres later; give me an in-memory version for the tests), and a `reassign` that loads a ticket, changes its assignee and saves it; reassigning a closed ticket is an error. Add tests, and make sure `cargo clippy --all-targets -- -D warnings` and `cargo test` pass.

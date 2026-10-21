---
tags: [skill-creator]
max_turns: 40
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

I'm starting a small Rust service called `mailer`. Create a cargo project (a library plus a binary) that reads its settings from the environment at startup: `MAILER_PORT` (the TCP port to listen on, never 0), `MAILER_ADMIN_EMAIL` (where alerts go) and `MAILER_RETRY_LIMIT` (1 to 10 retries). If anything is missing or malformed the service must refuse to start with a clear error. For now `main` just prints the parsed config. Add tests, and make sure `cargo clippy --all-targets -- -D warnings` and `cargo test` pass.

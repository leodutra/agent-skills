# rust-type-driven: machine checks through existing lints

The skill points to existing lints (rustc and clippy), configured in `skills/rust-type-driven/assets/lints.toml` and `assets/clippy.toml`. They hold every rule they can decide, and the model and review check only the rest (the Code Review Checklist). A lint is repeatable and cannot be talked out of a verdict, and existing lints cost a project nothing to install (the user's rule, memory `deterministic-checks-over-ai`).

## Rules

- Only lints that already exist in rustc or clippy. No custom-built tools, no extra installs.
- Every entry carries a comment: what it catches, and the rule and SKILL.md section it holds.
- Before a lint enters the skill, verify its name on the installed toolchain (`cargo clippy --explain <lint>`), and add a violation and a near miss to `fixtures/clippy/`.
- A rule a lint holds leaves the review part of the checklist.
- Development files stay here, out of `skills/`.

## Verify

`python3 dev/rust-type-driven/verify.py`: its docstring says what it checks. Run it after editing an asset or the template, and after a toolchain update.

## History

- 2026-09-26 to 2026-09-28: custom tooling was built, verified and pushed (up to `049b2e7`), then removed in `d23f64b` because the user prefers simple skills without much tooling. It was ast-grep rules, rejection coverage (cargo-llvm-cov and jq), dependency approval (jq and cargo-machete), and a dylint crate. `git show 049b2e7:dev/rust-type-driven/TODO.md` has the full record.
- The newtype guide (2026-09-28) sets the naming: the sole fallible constructor is `new`, and `try_new` exists only beside an infallible `new`.
- Considered, not added: rustc's `unused_crate_dependencies`, which reports every dependency a test target does not use.

## Left to the user

- Push.
- Toolchain parts installed for the removed tools, now unused: `rustup toolchain uninstall nightly-2026-08-20` (1,451 MB), and `rustup component remove llvm-tools-preview --toolchain stable` (26 MB).
- `~/Work/ed-galnet-scraper/skills/rust-type-driven` is a separate copy of the skill; this work does not update it.

# rust-type-driven: deterministic checks over review

Written 2026-09-26. The skill's rules are enforced by tools wherever a tool can decide them. A tool is repeatable and cannot be talked out of a verdict; review covers only what no tool can decide (the user's rule, memory `deterministic-checks-over-ai`).

Rules for every item:
- Name the rule, and the section of `skills/rust-type-driven/SKILL.md` it comes from.
- Verify the tool and every rule on a scratch crate before it enters the skill. A clean crate passes; one violation per rule fails; a near miss that is fine passes.
- Every rule or config entry in the skill carries a comment: what it catches, and the rule it holds.
- A rule a tool now holds leaves the review checklist.
- Development files stay here, out of `skills/`. Scratch crates live in `$TMPDIR` and are never committed.
- One commit per tier. Nothing is pushed until the user says so.
- `verify.py` re-checks every part the skill prints, from the skill's own text: `python3 dev/rust-type-driven/verify.py` (a missing tool binary: `AST_GREP=/path/to/ast-grep`). Each part gets fixtures under `fixtures/<part>/`, where a flagged line ends with `expect: <rule>`.

## Done

- [x] **T0. Compiler, clippy and a grep hold what they can** (`d7a24ac`, `5741b83`, not pushed). 20 lints, each verified on clippy 0.1.97 (now re-checked by `verify.py clippy`: 23 findings over 20 lints, near misses clean) and commented with what it catches and the rule it holds: panic policy, exhaustive matches, async discipline, ownership, bool flags, `anyhow` and `eyre` in libraries, interior mutability and ambient time or randomness in domain code, silenced lints only as `#[expect(..., reason)]`, and a CI grep for role names. The review checklist keeps only what no tool can decide.

## Tier 1: ast-grep rules (syntax patterns, milliseconds, no compiler internals)

Done 2026-09-26 on ast-grep 0.45.3: four rules in the skill, `ast-grep scan` a required command, `verify.py ast-grep` 13 findings of 13 expected, near misses clean. Decided on the way: domain code lives under a `domain` path, stated in Parse, Don't Validate; a fieldless enum may derive `Deserialize`, since every value it holds is valid; `tests/` may build string errors; an adapter error imported as a bare `Error` is not seen, so the skill says to write it with its path.

ast-grep is not installed here. Verify with its release binary in `$TMPDIR`; the skill tells projects how to install it.

- [x] **T1.1 A domain type deriving `Deserialize` without routing through its constructor.** Parse, Don't Validate: "Domain types MUST NOT derive `Deserialize` structurally". Rule: a struct or enum with `#[derive(..., Deserialize, ...)]` and no `#[serde(try_from = ...)]`, in the domain paths. Records and DTOs are named or placed so the rule can skip them: decide the convention (a path such as `src/domain/**`, or a `Dto`/`Request`/`Record` name suffix) and state it in the skill.
- [x] **T1.2 Stringly typed errors.** Error Modeling: "Code MUST NOT use `Err("something went wrong".into())`"; "Error variants MUST carry typed context". Rules: `Err($LIT.into())`, `Err($LIT.to_string())`, `Err(format!(...))`, and `Result<_, String>` in a signature.
- [x] **T1.3 An infrastructure error held without `#[source]` or `#[from]`.** Error Modeling: "keep the original as `#[source]` so the chain survives". Rule: an enum variant whose field is `std::io::Error` (and a configurable list such as `sqlx::Error`, `reqwest::Error`) without `#[source]` or `#[from]` on it.
- [x] **T1.4 Role names.** Behavior Rules: no `Service`, `Manager`, `Helper`, `Utils`, `Misc` types. Replaces the `rg` line: ast-grep matches the type name itself, so a comment or a string that mentions a name no longer counts.
- [x] **T1.5 Wire it in.** `sgconfig.yml` and the rule files as the skill shows them; `ast-grep scan` becomes a required command; the four rules leave the review checklist.

## Tier 2: dependencies

Done 2026-09-26: two commands in the skill's new Dependencies section, both required; `verify.py dependencies` 5 findings of 5 expected (an unapproved crate, an unused one, an empty reason, one that is both), clean cases clean, and both commands exit non-zero on findings.

- [x] **T2.1 Every dependency approved by name.** Philosophy: "The standard library SHOULD be preferred over new dependencies unless a crate provides clear value". Plan changed on the way: cargo-deny 0.20.2's `[bans] allow` list covers the whole crate graph, transitive crates included (its own template says "use with care"), so it cannot say "every crate *we* add". Instead each package lists its dependencies, dev and build ones too, under `[package.metadata.approved-dependencies]` with the reason each earns its place, and `cargo metadata --no-deps | jq` fails on any dependency with no reason or an empty one. Works offline, needs only jq. cargo-deny stays useful for licenses and advisories, which this skill does not cover.
- [x] **T2.2 Unused dependencies.** `cargo machete` (verified on 0.9.2; `cargo install cargo-machete`). It reads source, so a crate used only inside a macro's expansion looks unused: the skill says to list it under `[package.metadata.cargo-machete] ignored` with a comment saying why.
- [x] **T2.3 Wire it in.** Both are required commands (seven in all). The checklist keeps only the judgement the tools cannot make: "an approval reason the standard library answers? Remove the crate."

## Tier 3: mutation testing for the test budget

- [ ] **T3.1 Each constructor tested once per rejection reason.** Testing Strategy, Budget: "one accepted input and one rejected input, plus one rejected input per distinct reason for rejection". `cargo-mutants` (not installed: release binary in `$TMPDIR`) on the domain crate: a mutated guard that no test kills is a missing test. Verify: a constructor with a rejection reason that is not tested leaves a surviving mutant; adding the test kills it. Measure the run time on the scratch crate.
- [ ] **T3.2 Scope and cost.** Mutants only in domain code (`--file` or `mutants.toml` `examine_globs`), in CI or before a release, never on every save. State the time budget and the command in the skill.
- [ ] **T3.3 Wire it in.** The skill's Commands section gets it as a CI step; the checklist item becomes "surviving mutants in domain code are zero".

## Tier 4: dylint, type-aware custom lints (for a long-lived project)

Needs `cargo-dylint`, `dylint-link` and a pinned nightly toolchain, none installed. Heavier to keep up: dylint lints use rustc internals and break as rustc changes. Build them as a lint library under `dev/rust-type-driven/lints/`, and let a project adopt it; the skill says when it is worth it.

- [ ] **T4.0 Toolchain.** Install `cargo-dylint` and `dylint-link` and the nightly they need; record the versions. Ask before installing if it is more than a few hundred MB.
- [ ] **T4.1 Public fields on a type with a fallible constructor.** Type-Driven Design: "Fields of a type with an invariant MUST be private; a fallible constructor is the only way in." Rule: a struct with a `pub` field whose inherent impl has an associated function returning `Result<Self, _>`.
- [ ] **T4.2 Blocking calls inside `async fn`.** Async, Blocking work: "Async code MUST NOT block the runtime." Rule: a call to a listed blocking function (`std::fs::*`, `std::thread::sleep`, `std::net::*`, `std::io::stdin().read_line`) in the body of an `async fn` or `async` block, outside `spawn_blocking`.
- [ ] **T4.3 Raw primitives for domain concepts in signatures.** Philosophy and Core rules: a value with an invariant, or one that could be swapped with another of the same primitive, gets a newtype. Heuristic rule: a `pub fn` in domain code taking `String`, `&str`, `i64` or `Uuid` for a parameter named like `*_id`, `email`, `name`, `amount`. State it as a heuristic in the skill.
- [ ] **T4.4 A trait with a single implementor and no test double.** Dependency Injection: "A trait SHOULD NOT be introduced for a single implementation unless a real second implementation or test double is needed." Rule: a crate-local trait with exactly one `impl` in the crate, including `#[cfg(test)]` code; `pub` traits of a library are exempt.

## Stays with review (no tool can decide these)

A sentinel or a pair of `Option`s standing for exclusive states; validation after parsing; a `clone()` in a hot path that is needed but undocumented; an `assert!` guarding what should be a type; cancellation safety of async workflows.

## Left to the user

- Push `main` (`d7a24ac`, `5741b83` and this work are local).
- `~/Work/ed-galnet-scraper/skills/rust-type-driven` is a separate copy of the skill; it is not updated by this work.

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

Done 2026-09-26 on cargo-mutants 27.1.0: a Mutation testing section in the skill with `.cargo/mutants.toml` and `cargo mutants`; `verify.py mutants`: 16 mutants in about 2 s, the untested rejection guard found (1 line, 2 surviving mutants), the fully tested `try_new` and `try_from` constructors all caught, the untested getter out of scope; exit 2 gates CI.

- [x] **T3.1 Each constructor tested once per rejection reason.** Testing Strategy, Budget. Found on the way: cargo-mutants never looks inside a function named `new` (hard-coded in `src/visit.rs`, no switch), so a fallible `new` would never have its rejection tests checked. Decided: a fallible constructor is never named `new`, stated in Type-Driven Design; refined by the user on 2026-09-28: `try_new` when parsing is an implementation detail of construction (the caller hands over values), `parse` when the API conceptually exposes a parser (the caller hands over raw input); the `PriceCut` example became `try_new`; a fifth ast-grep rule, `fallible-new`, rejects a `new` returning `Result` (an `Option`-returning `new` stays legal). Also found: it mutates operators and function bodies, not method calls, so a guard that is one call (`if raw.is_empty()`) yields no mutant; the skill says so and the review checklist keeps that one case.
- [x] **T3.2 Scope and cost.** `examine_globs = ["src/domain/**/*.rs"]`, `examine_re` for `parse`, `try_new` and `try_from`, so a surviving mutant is exactly a missing rejection test and getters, which Testing Strategy says not to test, are never demanded. CI and before a release, not on every save.
- [x] **T3.3 Wire it in.** `cargo mutants` is the eighth required command, marked for CI. The checklist item on the constructor budget became its complement: "any test beyond the budget? Remove it."

## Tier 4: dylint, type-aware custom lints (for a long-lived project)

Done 2026-09-26 on cargo-dylint and dylint-link 6.1.0, nightly-2026-08-20: the library `rust_type_driven_lints` in `lints/`, four lints, each documented with what it catches and the rule it holds; a Type-aware lints section in the skill (when it is worth it, its cost, the adoption block, the command, one table row per lint, the silencing pattern); `verify.py dylint` 10 findings of 10 expected, near misses clean, the command gates CI. The checklist marks the four items dylint holds where it is adopted.

- [x] **T4.0 Toolchain.** Release binaries in `$TMPDIR` (3 MB and 1 MB). The pinned nightly with `rustc-dev` and `llvm-tools-preview` took 1,451 MB in `~/.rustup/toolchains` (`rustup toolchain uninstall nightly-2026-08-20` removes it); installing it also self-updated rustup from 1.29.0 to 1.29.1. The library builds in about 30 s once dependencies are cached.
- [x] **T4.1 `pub_field_on_invariant_type`.** A `pub` field on a struct with an associated fn returning `Result<Self, _>` or a `TryFrom` impl. Enum variant fields, always public, stay with review.
- [x] **T4.2 `blocking_in_async`.** A call whose path starts with `std::fs::`, `std::net::`, `std::thread::sleep`, a `std::process` wait or `std::io::stdin`, whose nearest enclosing closure is an async body; a closure such as `spawn_blocking`'s ends the search, so offloaded work is not flagged. Blocking through a trait method (`Read::read_to_string` on a `File`) is not seen.
- [x] **T4.3 `primitive_domain_param`.** A heuristic, stated as one in the skill: public fns in a module path containing `domain`, parameters named `id`, `*_id`, `email`, `name`, `amount`, typed `String`, `&str`, an integer or `uuid::Uuid`. Found on the way: on this compiler `String` is a language item, not a diagnostic item.
- [x] **T4.4 `single_impl_trait`.** Runs only when the crate is compiled for tests (`--all-targets`), where `#[cfg(test)]` doubles exist; traits exported from the crate are exempt.
- [x] **Silencing.** `#[cfg_attr(dylint_lib = "rust_type_driven_lints", expect(<lint>, reason = "…"))]`, with `unexpected_cfgs` taught the `dylint_lib` cfg; verified both ways: with the `check-cfg` line a plain `-D warnings` build passes, without it it fails.

Open: the library pins a nightly; when that nightly is updated, rebuild, run `verify.py dylint`, and move `rust-toolchain.toml` and the `clippy_utils` rev together. Projects point `[workspace.metadata.dylint]` at this repository's `dev/rust-type-driven/lints`, so it must be pushed before anyone can adopt it.

## Stays with review (no tool can decide these)

A sentinel or a pair of `Option`s standing for exclusive states; validation after parsing; a `clone()` in a hot path that is needed but undocumented; an `assert!` guarding what should be a type; cancellation safety of async workflows.

## Left to the user

- Push `main` (T0 to T4 are local commits). Projects can adopt the dylint library only after the push.
- `~/Work/ed-galnet-scraper/skills/rust-type-driven` is a separate copy of the skill; it is not updated by this work.

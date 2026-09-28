# rust-type-driven: deterministic checks over review

Written 2026-09-26. The skill's rules are enforced by tools wherever a tool can decide them. A tool is repeatable and cannot be talked out of a verdict; review covers only what no tool can decide (the user's rule, memory `deterministic-checks-over-ai`).

Rules for every item:
- Name the rule, and the section of `skills/rust-type-driven/SKILL.md` it comes from.
- Verify the tool and every rule on a scratch crate before it enters the skill. A clean crate passes; one violation per rule fails; a near miss that is fine passes.
- Every rule or config entry in the skill carries a comment: what it catches, and the rule it holds.
- A rule a tool now holds leaves the review checklist.
- Development files stay here, out of `skills/`. Scratch crates live in `$TMPDIR` and are never committed.
- One commit per tier. Nothing is pushed until the user says so.
- `verify.py` re-checks every part the skill prints, from the skill's own text, and the template in `references/newtypes.md`: `python3 dev/rust-type-driven/verify.py` (a missing tool binary: `AST_GREP=/path/to/ast-grep`). Each part gets fixtures under `fixtures/<part>/`, where a flagged line ends with `expect: <rule>`.

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

## Tier 3: mutation testing for the test budget (superseded 2026-09-28)

Replaced by rejection coverage (Newtype guide, below): the guide names the sole fallible constructor `new`, which cargo-mutants never examines. The record below is kept as history.

Done 2026-09-26 on cargo-mutants 27.1.0: a Mutation testing section in the skill with `.cargo/mutants.toml` and `cargo mutants`; `verify.py mutants`: 16 mutants in about 2 s, the untested rejection guard found (1 line, 2 surviving mutants), the fully tested `try_new` and `try_from` constructors all caught, the untested getter out of scope; exit 2 gates CI.

- [x] **T3.1 Each constructor tested once per rejection reason.** Testing Strategy, Budget. Found on the way: cargo-mutants never looks inside a function named `new` (hard-coded in `src/visit.rs`, no switch), so a fallible `new` would never have its rejection tests checked. Decided: a fallible constructor is never named `new`, stated in Type-Driven Design; refined by the user on 2026-09-28: `try_new` when parsing is an implementation detail of construction, whatever the input (the user's example: `try_new(input: &str)` that parses, validates and constructs), `parse` when the API conceptually exposes a parser; the `PriceCut` example became `try_new`; a fifth ast-grep rule, `fallible-new`, rejects a `new` returning `Result` (an `Option`-returning `new` stays legal). Also found: it mutates operators and function bodies, not method calls, so a guard that is one call (`if raw.is_empty()`) yields no mutant; the skill says so and the review checklist keeps that one case.
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

## Consistency pass, 2026-09-28

Prompted by the user: `Email` parses, yet under "parse, don't validate" it is constructed, so it is `try_new`; `parse` is for an API that exposes a parser. Read the whole skill for the same kind of slip and fixed each, test-first where a tool is involved; `verify.py` all five parts pass (clippy 24, ast-grep 18, dependencies 5, mutants 2, dylint 11).

- [x] **Names.** `Email::parse` and `CustomerId::parse` became `try_new`; the `parse` example is a real parser now (`Schedule::parse` for a cron expression, or `FromStr`); Parse, Don't Validate says that "parse" names the design, not the function. The Email comment said "No pub constructor" while `try_new` is one: it now says the field is private.
- [x] **A fallible constructor with any other name escaped mutation testing** (`Money::from_cents` in the proptest example). The rule now says a domain constructor's name says it can fail (`try_*`, `parse`, `FromStr`); a new ast-grep rule, `domain-constructor-name`, enforces it in domain paths only, since std's action names (`File::open`, `TcpStream::connect`) stay idiomatic in adapters; `fallible-new` still applies everywhere. The example became `try_from_cents`, and `examine_re` covers `try_*`, `parse` and `from_str`.
- [x] **`FromStr` was not a constructor to the tools.** Mutation testing now examines `from_str` (fixture: an untested guard in a `FromStr` impl is found); `pub_field_on_invariant_type` counts a `FromStr` impl, matched by path since this nightly has no diagnostic item for it.
- [x] **"Constructors accept `impl Into<String>`" contradicted `try_new(input: &str)`.** Now: owned-friendly when the constructor keeps its input, `&str` when it only reads it.
- [x] **"Every unsafe block documents its invariants" had no tool.** clippy's `undocumented_unsafe_blocks` is on, and the `forbid` comment says how a crate that needs unsafe lifts it (`forbid` cannot be lifted in code).
- [x] **The verifier hid an unloadable ast-grep rule** as zero findings; it now prints ast-grep's error.

## Newtype guide, 2026-09-28

The user supplied a newtype guide ("Rust newtypes: parse, don't validate") and said it overrides past definitions. It is adopted in SKILL.md and `references/newtypes.md`, adapted to the skill's other rules and to architecture-blueprint, and every rule a tool can decide got a tool. `verify.py`: all six parts pass (clippy 26, ast-grep 31, dependencies 5, coverage 4, dylint 20, template clean).

- [x] **Naming reverts to std's** (`abc6c72`). The sole fallible constructor is `new`, returning `Result` or `Option`; `try_new` only beside an infallible `new`; `parse` may exist and delegates to `FromStr`; named constructors for several formats (`from_hex`). This undoes the 2026-09-26 rule and the consistency pass's `try_*` naming: the ast-grep rules `fallible-new` and `domain-constructor-name` are removed.
- [x] **Tag and refinement.** A tag (`UserId(u64)`) has no invariant and a `pub` field; a refinement (`Email`, `Port`) has private fields and every rule. The guide allows a tag either; the skill picks the `pub` field so tools can tell the two apart. architecture-blueprint's identity newtype is a tag; its single-value value object is a refinement (one sentence in `domain-modeling.md`).
- [x] **The rest of the guide.** Parse, Don't Validate covers the edges (HTTP, CLI, config, DB decode, queues), domain signatures and yes/no validators. Type-Driven Design gets structure first (enums, `NonEmpty`, `NonZero*`, per-variant data, typestate), the constructor table, naming and invariant integrity. Error Modeling covers std errors with Send and Sync, derives, message style, `#[non_exhaustive]` and secrets. The panic policy admits `const fn literal`. Testing Strategy requires a `Display`/`FromStr` round-trip property test. `references/newtypes.md` holds serde, clap, database and std trait rules, plus the template.
- [x] **The template obeys the skill.** Formatted by rustfmt; `literal` carries `#[expect(clippy::panic, reason)]`; the budget's tests are included. `verify.py template` runs fmt, clippy, ast-grep and rejection coverage on it, and a broken copy fails (checked once).
- [x] **ast-grep** (`77be2d5`). `refinement-bypass` replaces `domain-structural-deserialize` (a private-field struct with Deserialize not via `try_from`, or with serde or sqlx `transparent`). New rules: `refinement-default`, `newtype-derives`, `validation-predicate`, `infallible-try-from`, `try-new-without-new`, `literal-outside-const`, `error-message-style` and `domain-error-derives`. Shared patterns are global utils (`utilDirs`). Verified: a suppression is `// ast-grep-ignore: <rule> -- <reason>` on the line directly above the matched node, after the attributes; one placed above the attributes does not apply.
- [x] **clippy** (`9357a4c`): `missing_debug_implementations` (rustc) and `derive_partial_eq_without_eq`.
- [x] **Rejection coverage replaces cargo-mutants** (`c12afdf`). ast-grep lists each `Err(..)` in domain code and each `None` in a function returning `Option`. `cargo llvm-cov --json` records region counts, and a jq join fails on a rejection whose region never ran. Region, not line: a one-line `if n == 0 { None } else { .. }` is judged on its own. It also sees one-call guards (`is_empty()`) and forbidden transitions, which mutation testing missed. It cannot see `?` or `ok_or`, nor whether a test asserted; review keeps both. Setup: `rustup component add llvm-tools-preview` added 26 MB to stable here; cargo-llvm-cov 0.9.1 release binary is in `/tmp/claude-1000/tools`.
- [x] **dylint** (`292fc14`). `pub_field_on_invariant_type` counts `new` returning `Option<Self>`, and no longer counts methods taking `self` (transitions). New lints: `refinement_escape` (`Deref`, `DerefMut`, `AsMut`, `BorrowMut`, or a pub `&mut` method on a type with a fallible constructor) and `error_not_std_error` (`()` or a local type without `Error + Send + Sync` as a public fn's error or a `FromStr`/`TryFrom` impl's). `sym::Error` comes from `clippy_utils::sym`, not rustc's.
- [x] **Docs aligned.** blueprint `Port(u16)` became `Port(NonZeroU16)`, and its identity newtype example has a `pub` field. `docs/RUST_BACKEND_STACK.md`'s `newtypes/` folder became `domain/`, as the blueprint requires.

## Stays with review (no tool can decide these)

A sentinel or a pair of `Option`s standing for exclusive states; validation after parsing; a `clone()` in a hot path that is needed but undocumented; an `assert!` guarding what should be a type; cancellation safety of async workflows. From the guide: validation duplicated instead of delegated; `Option` for more than one failure; checking before normalizing; a mutator that can break the invariant; a `Display`/`FromStr` pair without its round-trip test; secrets in `Debug`, `Display`, `Serialize` or messages; a hand-written `Borrow` that disagrees with `Eq`/`Hash`; a rejection through `?` or `ok_or`, and a test that reaches a rejection without asserting on it.

## Left to the user

- Push `main`: the newtype guide's six commits, from abc6c72 on, are local. Projects get the new dylint lints only after the push.
- `llvm-tools-preview` is now installed on stable (26 MB); `rustup component remove llvm-tools-preview --toolchain stable` undoes it.
- `~/Work/ed-galnet-scraper/skills/rust-type-driven` is a separate copy of the skill; it is not updated by this work.

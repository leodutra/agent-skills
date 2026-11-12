---
name: rust-style-guide
description: >
  Type-driven Rust style for domain and backend code, with a clippy/rustc lint set that enforces
  much of it: refinement newtypes that parse instead of validate, illegal states unrepresentable,
  Option for absence and Result for failure, precise thiserror errors, total functions, async
  cancellation safety, invariant tests. Use when writing, reviewing, refactoring or designing Rust
  that models a domain or business rules (HTTP/RPC handlers, config, CLI args, database rows, state
  machines, value objects, error types), on mentions of newtype, refinement type, parse don't
  validate, validation, domain model, illegal states, typestate, thiserror, anyhow, TryFrom, FromStr,
  NonZero, serde try_from or transparent, clap value types, sqlx decode, Result/Option design, tokio
  tasks, spawn_blocking, cancellation safety, proptest or clippy lints, and when Rust under review
  has raw String/i64/Uuid in signatures, `is_valid_*` or `validate` checks, stringly typed errors,
  `_ =>` on its own enums, or unwrap()/expect() outside tests. GPU/render code:
  rust-wgpu-functional; Bevy ECS: rust-bevy-architecture.
---

# Rust style guide

These rules override default Rust conventions; a documented project decision may override them.
Read `MUST`, `SHOULD` and `MAY` literally. The reasons, for people, are in
[references/fundamentals.md](references/fundamentals.md); don't load it to write or review code.

## Workflow

**Writing code**
1. Apply the lints first: paste [assets/lints.toml](assets/lints.toml) into `Cargo.toml` (in a
   workspace, as `[workspace.lints.*]` with `lints.workspace = true` in each member) and copy
   [assets/clippy.toml](assets/clippy.toml) to each crate's root, without the entries its comments
   limit to other kinds of crate.
2. Model the types before the functions: a refinement per value with an invariant, an enum per set
   of states, an error type per set of failures.
3. Silence a lint misfire where it happens, with `#[expect(clippy::name, reason = "…")]`; never edit
   the lint set to get a build through.
4. Done when `cargo check`, `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings` and
   `cargo test` pass.

**Reviewing code**
1. If CI runs this lint set, don't report what the lints hold (see [Lints](#lints)); otherwise
   report those too.
2. Check every rule below against the code.
3. Check each finding against [Allowed](#allowed-not-defects): what is listed there is not a
   defect, not even a nit.
4. Report each problem with its line, the rule it breaks, why it matters and the fix.

## Refinements: parse, don't validate

A raw value becomes its refinement as soon as it is read; from then on the type is the proof. Every
refinement has this shape:

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, serde::Serialize, serde::Deserialize)]
#[serde(try_from = "u16", into = "u16")] // deserializing goes through the constructor
pub struct Port(NonZeroU16); // private field, built on std's NonZeroU16

#[derive(Debug, Clone, Copy, PartialEq, Eq, thiserror::Error)]
#[error("port must be non-zero")]
pub struct ZeroPort; // the constructor's only failure, so a unit struct

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ParsePortError { // text adds a syntax failure in front of the constructor's own
    #[error("invalid port number: {0}")]
    Syntax(#[from] ParseIntError),
    #[error(transparent)]
    Zero(#[from] ZeroPort),
}

impl Port {
    pub const fn new(n: u16) -> Result<Self, ZeroPort> { // the one validating constructor
        match NonZeroU16::new(n) {
            Some(n) => Ok(Self(n)),
            None => Err(ZeroPort),
        }
    }

    #[must_use]
    #[expect(clippy::panic, reason = "a compile-time literal: an invalid value fails compilation")]
    pub const fn literal(n: u16) -> Self { // const items only
        match Self::new(n) {
            Ok(port) => port,
            Err(ZeroPort) => panic!("port must be non-zero"),
        }
    }
}

impl TryFrom<u16> for Port { /* Self::new(n) */ }
impl From<Port> for u16 { /* port.0.get() */ }
impl FromStr for Port { /* Ok(Self::new(s.parse()?)?) */ }
impl fmt::Display for Port { /* self.0.fmt(f): the exact inverse of FromStr */ }

pub const HTTP: Port = Port::literal(80);
```

- Code MUST NOT re-check the invariant, and functions MUST take the refinement (`Email`), never
  the primitive it came from (`&str`). A yes/no check (`is_valid_x(&str) -> bool`, `validate(&self)`
  over public fields) MUST become the refinement's constructor.
- One validating constructor; every way in delegates to it: `FromStr` (with `Display` as its exact
  inverse) for text, `TryFrom<String>` too when the value keeps the string, `TryFrom<u16>` and so on
  for one non-string source, `impl TryFrom<Dto>` for a record, row or DTO deserialized as is.
- The sole fallible constructor MUST be named `new` (as `NonZero::new`, `CString::new`); `try_new`
  exists only beside an infallible `new`. It returns `Result`, never `Option` (which means absence).
- Its error holds only the failures that constructor can produce: a unit struct for one, an enum
  for several. Two constructors MUST NOT share an error enum when either can't produce all its
  variants (`Email::new` and `DisplayName::new` each get their own). `FromStr` wraps that error
  beside its own syntax failure.
- The constructor normalizes first (trim, canonical case), so `Eq`/`Hash`/`Ord` compare canonical
  values, without collapsing a distinction the domain keeps: an email lowercases its domain and
  keeps the part before the `@` as typed.
- No `Deref`/`DerefMut`, no `&mut` to the inner value; offer `as_str()`, `get()`, `AsRef` or
  `into_inner()`. A mutating method keeps the invariant or does not exist. No `Default` unless the
  default is valid. Build on std's types where they hold the invariant.
- serde: `#[serde(try_from = "String", into = "String")]` (or `"u16"`, …) backed by `TryFrom` and
  `From<Self> for Inner`. A derived `Deserialize`, `#[serde(transparent)]` or `#[sqlx(transparent)]`
  on a refinement skips the constructor and MUST NOT be used; a database `Decode`/`FromSql` decodes
  the inner type and calls `try_from`.
- clap: a refinement field parses through `FromStr`, with no custom `value_parser`;
  `default_value_t = CONST` prints with `Display` and parses back, so the round trip must hold.
- Derive `Debug, Clone, PartialEq, Eq, Hash` (`Copy` when the inner type is); `Borrow<str>` only
  when the derives agree with `str`'s. `Eq` adds reflexivity (`a == a` for every value) to
  `PartialEq`'s symmetry and transitivity; the compiler cannot check it, so derive `Eq` (it compiles
  only when every field is `Eq`), never hand-write it over a `PartialEq` that breaks it (`f32`/`f64`
  are not `Eq`: `NaN != NaN`).
- A secret hand-writes a redacted `Debug`, with no `Display` and no `Serialize`.
- A compile-time literal is a `const fn literal` that calls `new` and panics on its failure, under
  `#[expect(clippy::panic, reason = "…")]`, called only in `const` items. It never builds `Self`
  directly.

## Types

- Illegal states MUST be unrepresentable: exclusive states are one enum, not `bool` flags, `Option`s
  or a string; fields that exist only together are one variant's data; a number that cannot be zero
  is `NonZero*`. State read from storage or the wire is an enum, not typestate.
- `Option` means absence, `Result` means failure; neither stands in for the other (no `.ok()` that
  drops an error). A lookup that can fail returns `Result<Option<T>, E>`: `Ok(None)` is not found,
  `Err` the store failing. An operation that needs the value makes its absence an error variant. A
  function that cannot fail returns a plain `Option` for "nothing here".
- Absence is an `Option` with one meaning, or a variant; sentinels (`""`, `0`, `-1`) MUST NOT stand
  for it.
- A value gets a newtype when it carries an invariant or could be swapped with another value of the
  same primitive. A **tag** (`UserId(u64)`) has no invariant: its field is `pub`, and `From` and
  `#[serde(transparent)]` are fine. A **refinement** (`Email`, `Port`) has one: its fields MUST be
  private.
- A closed set is a `ValueEnum` (clap) or a `rename_all` enum (serde), not a refinement over a
  string.
- Data with more than one field has named fields: no tuples or tuple structs beyond a newtype.
- Variant fields are public, so fields sharing an invariant (`start < end`) MUST sit in a
  private-field struct with a validating constructor, which the variant wraps.

## Errors

- Library errors are typed (`thiserror` enums, or a unit struct for a single failure) implementing
  `Error + Send + Sync + 'static`, with typed context (`InvalidTransition { from, to }`); `String`,
  `&str` and `()` MUST NOT be errors or carry their context. `anyhow`/`eyre` stay at process
  boundaries, with `.context(...)`.
- A public function's error MUST NOT be a dependency's error type raw: wrap it in a variant of your
  own and keep it as `#[source]`.
- Derive `Clone, PartialEq, Eq` (reflexive, as above) unless a cause cannot (`io::Error`), so tests
  assert on variants.
- Messages are lowercase, with no trailing period, say what is wrong, and never echo secret input
  (an `InvalidToken` does not hold the token).

## Behavior

- Functions are total; code MUST NOT panic on valid input or validate user input with `assert!`.
  `panic!`, `unwrap()` and `expect()` MUST NOT appear outside tests, except `expect()` with a clear
  message in `main.rs` bootstrap under `#[expect(clippy::expect_used, reason = "…")]`.
- Match exhaustively on your own enums: no `_ =>` arm, and no `#[non_exhaustive]` on them (it forces
  `_` arms in the workspace's other crates); it belongs only in a crate published to users you
  don't rebuild.
- Time and randomness are parameters in domain logic, never ambient (`Utc::now()`, `rand`).
- Domain types hold no interior mutability; prefer `&mut self`, leaving sharing to the caller.
- No `Service`, `Manager`, `Helper`, `Utils`, `Misc` names; a trait is named for what it does
  (`LoadOrders`), and it needs a second implementation or a test double to exist.
- A macro is the last resort: a function, type or trait first, then `macro_rules!`, then a proc
  macro.

## Async

- A trait whose futures are spawned multithreaded declares `-> impl Future<Output = …> + Send`.
- No `std::sync::MutexGuard` across `.await`; no blocking calls on the runtime (`std::fs`, sync
  clients, heavy CPU work): use async APIs or `spawn_blocking`.
- Every `.await` is a cancellation point: a future dropped there MUST NOT leave an effect half done
  (a charge made but not recorded).

## Tests

- One accepted input per constructor, and every rejection reason in domain code reached by a test
  that asserts its specific error (`assert_eq!(Port::new(0), Err(ZeroPort))`). No second example of
  a rule already pinned, and no tests of derives, getters or what the compiler guarantees.
- Where a law exists, a property test replaces examples; a type with `Display` and `FromStr` MUST
  have one that its `Display` parses back:

  ```rust
  proptest! {
      #[test]
      fn port_display_parses_back(n in 1u16..) {
          let port = Port::try_from(n)?;
          prop_assert_eq!(port.to_string().parse::<Port>(), Ok(port));
      }
  }
  ```

- Each forbidden state transition the types cannot rule out is tested. Integration tests in `tests/`
  use the public API.

## Allowed: not defects

These follow the rules above. In review, don't flag them, not even as nits:
- A tag's `pub` field, `From` impl or `#[serde(transparent)]`.
- `Result<Option<T>, E>` from a lookup; a plain `Option` from a function that cannot fail.
- A unit-struct error for a constructor with one failure; `try_new` beside an infallible `new`.
- An error without `Clone`/`PartialEq`/`Eq` because a cause lacks them (`io::Error`).
- `#[non_exhaustive]` in a crate published to users you don't rebuild.
- The panic in a `const fn literal` called in `const` items, under its `#[expect]`.
- `expect()` with a clear message in `main.rs` bootstrap, under its `#[expect]`.
- `unwrap()`, `expect()`, `panic!` in `#[test]` functions and `#[cfg(test)]` code.
- `anyhow`/`eyre`, the clock, randomness and locks outside domain and library code (a binary's
  `main`, infrastructure), where clippy.toml's comments exempt them.

## Lints

What clippy can check, clippy checks. The test allowances cover `#[test]` functions and
`#[cfg(test)]` code; a helper under `tests/` is neither, so it returns `Result` and uses `?`.

The lints hold: wildcard arms, unwrap/expect/panic outside tests, unsafe, missing `Debug`/`Eq`,
infallible `TryFrom`, a `Result` that never fails, mixed `pub` fields, `Option<Option<T>>`,
non-`Send` futures, locks across `.await`, more than three bools, glob imports, `for_each`,
`&Option` parameters, `map_err(|_| …)`, a dropped `Result`, `assert!(r.is_err())`, `anyhow`/`eyre`,
`Cell`/`RefCell`/`Mutex`/`RwLock`, the banned clock, `rand` and `uuid` calls, `catch_unwind`.

Review must also catch what no lint bans: atomics and `OnceCell` in domain code; an unused
dependency; an `.ok()` whose `None` hides an error; a test that reaches a rejection without
asserting its error in a form the lint misses.

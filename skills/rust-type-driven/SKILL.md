---
name: rust-type-driven
description: >
  Idiomatic type-driven Rust for domain and backend code: parse-don't-validate at trust
  boundaries, newtypes for domain concepts, illegal states unrepresentable, typed errors
  with thiserror, capability traits, async/cancellation discipline, and invariant testing.
  Use this skill whenever writing, reviewing, refactoring, or designing Rust that models a
  domain — HTTP/RPC handlers, database or queue boundaries, state machines, value objects,
  error types. Trigger on mentions of: parse don't validate, newtype, refinement type,
  illegal states, typestate, thiserror, anyhow, TryFrom, FromStr, NonZero, serde try_from or
  transparent, clap value types, sqlx decode, domain model, validation, Result or Option design,
  trait/DI decisions, tokio tasks, cancellation safety, spawn_blocking, proptest. Also trigger
  when Rust code under review uses raw String/i64/Uuid in signatures, `is_valid_*` or `validate`
  checks, stringly typed errors, `_ =>` arms on its own enums, or unwrap()/expect() outside tests.
  For GPU/render/performance-critical Rust use rust-wgpu-functional; for Bevy ECS layout
  use rust-bevy-architecture.
---

# Rust — Idiomatic Type-Driven Patterns

These rules override default Rust conventions in the project; an ADR may override them. Read
`MUST`, `SHOULD` and `MAY` literally.

## Parse, don't validate

External data (HTTP, RPC, CLI, config, database rows, queues, files, environment) is parsed once,
where it enters, into a domain type; from then on the type is the proof.

- Code MUST NOT re-check an invariant after parsing. Domain functions MUST take the domain type
  (`Email`), never the primitive it came from (`&str`).
- A yes/no check (`is_valid_x(&str) -> bool`, `validate(&self)` over public fields) MUST be replaced
  by a constructor that returns the type.
- A record, row or DTO is deserialized as is and converted with `impl TryFrom<Dto> for Domain`.
- Domain code SHOULD live under a `domain` path, DTOs elsewhere.

## Types

- Illegal states MUST be unrepresentable: exclusive states are one enum, not `bool` flags,
  `Option`s or a string; fields that exist only together are one variant's data; a number that
  cannot be zero is `NonZero*`. State read from storage or the wire is an enum, not typestate.
- Absence is an `Option` with one meaning, or a variant; sentinels (`""`, `0`, `-1`) MUST NOT stand
  for it.
- A value gets a newtype when it carries an invariant or could be swapped with another value of the
  same primitive. A newtype is one of two kinds, and its field says which:
  - A **tag** (`UserId(u64)`) has no invariant: its field is `pub`, and `From` and
    `#[serde(transparent)]` are fine.
  - A **refinement** (`Email`, `Port`) has one: its fields MUST be private.
- Variant fields are public, so fields sharing an invariant (`sale < regular`) MUST sit in a
  private-field struct the variant wraps.

### Refinements

- One validating constructor, and every way in delegates to it: `FromStr` (with `Display` as its
  exact inverse) for text, `TryFrom<String>` too when the value keeps the string, `TryFrom<u16>`
  and so on for one non-string source, `impl TryFrom<Dto>` for a payload.
- The sole fallible constructor MUST be named `new` (as `NonZero::new`, `CString::new`); `try_new`
  exists only beside an infallible `new`. It returns `Option` only for one self-evident failure
  (zero, empty); otherwise `Result` with a dedicated error enum.
- The constructor normalizes first (trim, canonical case), so `Eq`/`Hash`/`Ord` compare canonical
  values, without collapsing a distinction the domain keeps.
- No `Deref`/`DerefMut`, no `&mut` to the inner value; offer `as_str()`, `get()`, `AsRef` or
  `into_inner()`. A mutating method keeps the invariant or does not exist. No `Default` unless the
  default is valid. Build on std's where it holds the invariant (`Port(NonZeroU16)`).
- serde: `#[serde(try_from = "String", into = "String")]` (or `"u16"`, …) backed by `TryFrom` and
  `From<Self> for Inner`. A derived `Deserialize`, `#[serde(transparent)]` or `#[sqlx(transparent)]`
  on a refinement skips the constructor and MUST NOT be used; a database `Decode`/`FromSql`
  decodes the inner type and calls `try_from`.
- clap: a field of the refinement type parses through `FromStr`, with no custom `value_parser`;
  `default_value_t = CONST` prints with `Display` and parses back, so the round trip must hold. A
  closed set is a `ValueEnum` (clap) or a `rename_all` enum (serde), not a refinement over a string.
- Derive `Debug, Clone, PartialEq, Eq, Hash` (`Copy` when the inner type is); `Borrow<str>` only
  when the derives agree with `str`'s. A secret hand-writes a redacted `Debug`, with no `Display` and
  no `Serialize`.
- A compile-time literal is `const fn literal(..) -> Self` that calls `new` and panics on its
  failure, called only in `const` items, under `#[expect(clippy::panic, reason = "…")]`.

## Errors

```rust
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum OrderError {
    #[error("cannot transition from {from} to {to}")]
    InvalidTransition { from: OrderStatus, to: OrderStatus },
    #[error("order store unavailable")]
    StoreUnavailable(#[source] StoreError),
}
```

- Library errors are typed enums (`thiserror`) implementing `Error + Send + Sync + 'static`, with
  typed context; `String`, `&str` and `()` MUST NOT be errors or carry their context. `anyhow`/`eyre`
  stay at process boundaries, with `.context(...)`.
- Derive `Clone, PartialEq, Eq` unless a cause cannot (`io::Error`), so tests assert on variants.
- Messages are lowercase, with no trailing period, say what is wrong, and never echo secret input.
- An infrastructure error MUST NOT cross a domain or capability boundary raw: translate it there and
  keep it as `#[source]`.

## Behavior

- Functions are total; code MUST NOT panic on valid input or validate user input with `assert!`.
- Match exhaustively on your own enums: no `_ =>` arm.
- Time and randomness are parameters in domain logic, never ambient (`Utc::now()`, `rand`).
- Domain types hold no interior mutability; prefer `&mut self`, leaving sharing to the caller.
- No `Service`, `Manager`, `Helper`, `Utils`, `Misc` names; traits name capabilities
  (`LoadOrders`), and a trait needs a second implementation or a test double to exist.
- A trait whose futures are spawned multithreaded declares `-> impl Future<Output = …> + Send`.
- Async: no `std::sync::MutexGuard` across `.await`; no blocking calls on the runtime (use async APIs
  or `spawn_blocking`); every `.await` is a cancellation point, so money, inventory or external
  effects are idempotent or transactional.
- `panic!`, `unwrap()`, `expect()` MUST NOT appear outside tests, except `expect()` with a clear
  message in `main.rs` bootstrap under `#[expect(clippy::expect_used, reason = "…")]`.

## Tests

- One accepted input per constructor, and every rejection reason in domain code reached by a test
  that asserts its specific error. No second example of a rule already pinned, and no tests of
  derives, getters or what the compiler guarantees.
- Where a law exists, a property test replaces examples; a type with `Display` and `FromStr` MUST
  have one that its `Display` parses back.
- Each forbidden state transition the types cannot rule out is tested. Integration tests in `tests/`
  use the public API.

```rust
proptest! {
    #[test]
    fn port_display_parses_back(n in 1u16..) {
        let port = Port::try_from(n)?;
        prop_assert_eq!(port.to_string().parse::<Port>(), Ok(port));
    }
}
```

## Lints

What clippy can check, clippy checks. Paste [assets/lints.toml](assets/lints.toml) into
`Cargo.toml` and copy [assets/clippy.toml](assets/clippy.toml) to each crate's root, without the
entries its comments limit to other kinds of crate. Silence a misfire where it happens with
`#[expect(clippy::name, reason = "…")]`. The test allowances cover `#[test]` functions and
`#[cfg(test)]` code; a helper under `tests/` is neither, so it returns `Result` and uses `?`.

In review, the lints hold what their comments name (wildcard arms, unwrap/expect/panic outside
tests, unsafe, missing `Debug`/`Eq`, infallible `TryFrom`, mixed `pub` fields, non-`Send` futures,
locks across `.await`, more than three bools, `anyhow`/`eyre`, `Cell`/`RefCell`/`Mutex`/`RwLock`,
the banned clocks and `rand` calls). Review every other rule above, plus what no lint bans
(atomics, `OnceCell`, `Uuid::new_v4` in domain code; an unused dependency; a test that reaches a
rejection without asserting its error).

`cargo check`, `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings` and `cargo test`
MUST pass before a task is done.

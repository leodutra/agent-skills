---
name: rust-style-guide
description: >
  Rust style guide and lint set: the default for all Rust code, for every change to or review of it,
  however small. Invoke before reviewing Rust (a PR, diff or file that touches `.rs`: the guide is
  the review checklist) and before writing, adding, modifying, fixing, refactoring, renaming,
  debugging or designing it: any `.rs` file, even a one-line fix or a mechanical rename, plus
  `Cargo.toml` lint tables and clippy configuration, in any kind of crate or framework. Covers
  refinement newtypes that parse instead of validate, illegal states unrepresentable, typed errors,
  total functions, borrowed inputs, async safety and invariant tests.
argument-hint: "[review [path|PR|diff] · audit · lint [path|crate] · <task>]"
---

# Rust style guide

Default for all Rust, over Rust's own defaults. A documented project decision (`CLAUDE.md`, ADR,
project docs; never a code comment) or more specific guidance for the code at hand (a framework's
conventions, another loaded skill) wins only on the point and scope it names. `MUST`/`SHOULD`/`MAY`
are literal. Reasons, for people: [references/fundamentals.md](references/fundamentals.md) (don't
load).

**When rules pull apart**, the first wins: memory and type safety; domain invariants; semantic
clarity (an obvious API over a conforming one); std-trait interoperability; simplicity;
performance; style. A documented project requirement (a hard deadline, a stable public API) MAY
override a convention, never safety or an invariant. Performance overrides a convention only with
a measurement or a stated system constraint, documented where the code deviates.

**Proportionality**: a newtype, trait, error variant, layer or generic parameter exists only when it
enforces an invariant, prevents a real misuse, names a domain concept or measurably eases
maintenance; never for uniformity. These rules say how such a thing is built, not that every value
needs one.

**Terms**
- **Boundary**: anywhere data from outside the program enters, or re-enters from storage or the
  wire.
- **Domain code**: library and domain logic; not a binary's `main` or infrastructure.
- **Tag**: a newtype with no invariant; every value of its primitive is valid. **Refinement**: any
  type with an invariant, one field or several (`Email`; a `Span` whose `start < end`).

## Workflow

- `review [target]` → **Review** (default: the current diff).
- `audit` → **Review** of the whole codebase, findings grouped by rule, most severe first.
- `lint [target]` (code or crates; default: the workspace) → **Write** step 1 for the owning crates
  if missing, then clippy with `-D warnings` on them, each finding inside the target fixed by step 3.
- Other text, or none → the task, via **Write**.

**Write**
1. Lints: paste [assets/lints.toml](assets/lints.toml) into `Cargo.toml` (workspace:
   `[workspace.lints.*]` + `lints.workspace = true` per member), copy
   [assets/clippy.toml](assets/clippy.toml) to each crate root, follow both files' comments.
2. Types before functions: a refinement per value with an invariant, an enum per set of states, an
   error type per set of failures.
3. A lint misfire gets `#[expect(clippy::name, reason = "…")]` where it happens; never edit the lint
   set to get a build through.
4. Done: `cargo check`, `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`,
   `cargo test` pass.

**Review**: skip what [the lints hold](#lints) if CI runs them, else report it too; check every
rule; drop anything [Allowed](#allowed), not even a nit; report line, rule, why, fix.

## Types

- Illegal states MUST be unrepresentable: exclusive states are one enum (not `bool`s, `Option`s, a
  string); fields that exist only together are one variant's data; never-zero is `NonZero*`. State
  from storage or the wire is an enum, not typestate.
- `Option` is absence, `Result` failure; neither stands in for the other (no `.ok()` dropping an
  error). A fallible lookup returns `Result<Option<T>, E>` (`Ok(None)` not found, `Err` the store
  failing); an operation that needs the value makes absence an error variant; a lookup that can't
  fail returns `Option`. One meaning per `Option`; sentinels (`""`, `0`, `-1`) MUST NOT stand for
  absence.
- A value with an invariant, or swappable with another of the same primitive, gets a newtype. A
  refinement's fields MUST be private to its defining module (not `pub(crate)`). A tag's field is
  `pub`, with `From` and `#[serde(transparent)]` fine where the two types make the meaning obvious
  (`From<u64> for UserId`, `From<u32> for Grams`), never where the primitive carries a unit or
  scale the target doesn't name (`From<u64> for Timestamp`). A function takes the newtype itself,
  never `impl Into<Newtype>`, which lets the bare primitive back in.
- A closed set is an enum, not a refinement over a string. Its `ValueEnum` (clap) or `rename_all`
  (serde) names are its canonical text; code that parses that text itself does so in a `FromStr`
  that accepts the same names.
- More than one field means named fields: no tuples or tuple structs beyond a newtype.
- Variant fields are public, so fields sharing an invariant MUST sit in a refinement the variant
  wraps.

**Making a value from another** (every type): what the source is decides.
- **Conversion**: one typed value becomes unambiguously the same value in another type, with
  nothing lost, rounded or chosen; wrapping a primitive without a check (a tag) counts. `From` when
  it can't fail, `TryFrom` when it fails rather than lose anything (into a refinement, narrowing a
  number; never `as`). A primitive whose type doesn't carry its unit is ambiguous, so no trait: a
  named constructor says the unit where the raw number enters (`from_grams`); once quantities
  travel through the domain where units could be swapped, they get a unit type (the newtype rule)
  and convert by these rules (`From<Grams> for Weight`); a unit change that rounds (grams to whole
  ounces) is a named method (`Grams::to_whole_ounces`). A conversion that would surprise a reader of
  `.into()` is never a trait: a named function says what it does. A constructor taking several
  values is not a conversion.
- **Parsing**: interpreting a text or byte representation by a grammar or encoding. Complete text
  with one unambiguous interpretation as an owned value MUST parse through `FromStr`, whatever else
  the type offers; it may accept several spellings, while `Display` prints one. `TryFrom<&str>` and
  `TryFrom<String>` MAY sit beside it with the same semantics (an owned `TryFrom<String>` MAY keep
  its allocation), never replace it. A type that borrows its input uses `TryFrom<&'a str>` or a
  named parser. Complete bytes with one context-free interpretation MAY use `TryFrom<&[u8]>`;
  otherwise (byte order, version, policy, borrowing, streaming) a named decoder.
- A parse that extracts (part of the input, or many values) is a named function that says what it
  takes (`parse_query`), or a collection type with `FromStr` when the whole input is one
  collection. A parse that chooses among formats, policies or interpretations is a named function
  that says the choice (`from_json`).
- For an unambiguous conversion or a complete text parse, a name MUST NOT replace the trait
  (`Foo::from_u16` with no `TryFrom<u16>` is a defect); it MAY sit beside it. Where the trait would
  hide a loss, a rounding, an ambiguity or a policy, the named function says so in its doc comment;
  merely describing the input is not a reason.

## Refinements: parse, don't validate

At every boundary, data is parsed into domain types before domain logic; from then on the type is
the proof. The boundary type is itself built from domain types: a request, row or DTO field whose
value has a refinement or tag MUST use it, so deserializing runs its constructor, and no primitive
travels past the boundary. A separate DTO, still built from domain types, exists only when the
wire's shape differs, or as the mirror serde needs to reach a cross-field constructor
(`#[serde(try_from = "Raw")]`); its `TryFrom` calls the domain type's constructor.

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, serde::Serialize, serde::Deserialize)]
#[serde(try_from = "u16", into = "u16")] // deserializing goes through the constructor
pub struct Port(NonZeroU16); // private field

#[derive(Debug, Clone, Copy, PartialEq, Eq, thiserror::Error)]
#[error("port must be non-zero")]
pub struct ZeroPort; // the only failure: a unit struct

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ParsePortError { // text adds a syntax failure before the constructor's
    #[error("invalid port number: {0}")]
    Syntax(#[from] ParseIntError),
    #[error(transparent)]
    Zero(#[from] ZeroPort),
}

impl Port {
    pub const fn try_new(n: u16) -> Result<Self, ZeroPort> { // the one validating constructor
        match NonZeroU16::new(n) {
            Some(n) => Ok(Self(n)),
            None => Err(ZeroPort),
        }
    }

    #[must_use]
    #[expect(clippy::panic, reason = "a compile-time literal: an invalid value fails compilation")]
    pub(crate) const fn literal(n: u16) -> Self { // const items only
        match Self::try_new(n) {
            Ok(port) => port,
            Err(ZeroPort) => panic!("port must be non-zero"),
        }
    }
}

impl TryFrom<u16> for Port { /* Self::try_new(n) */ }
impl From<Port> for u16 { /* port.0.get() */ }
impl FromStr for Port { /* Ok(Self::try_new(s.parse()?)?) */ }
impl fmt::Display for Port { /* self.0.fmt(f): FromStr parses it back */ }

pub const HTTP: Port = Port::literal(80);
```

- Code MUST NOT re-check the invariant; functions MUST take the refinement, never its primitive. A
  yes/no check (`is_valid_x(&str) -> bool`, `validate(&self)` over public fields) MUST become the
  constructor.
- No value of the type exists that breaks its invariant. One validation, and every way in runs it:
  `FromStr` (its output printed back by `Display`), text and primitive `TryFrom`, serde, database
  decoders. A cross-field rule lives there, never only in a DTO's `TryFrom`. Every other
  way to obtain a value (`Default`, mutation, operators, feature-gated or test-only APIs) keeps the
  invariant; an operation that can break it is a `try_*` method returning `Result`, never an
  operator.
- An inherent fallible constructor MUST be `try_new`, returning `Result`, never `Option`; `new`
  can't fail. Other names follow C-CTOR: an I/O resource's domain verb (`open`, `connect`,
  `bind`), `with_*` for a secondary constructor, `from_*` only for a parse that chooses; a
  conversion is the trait, and a name only sits beside it.
- Its error holds only the failures it can produce: a unit struct for one, an enum for several.
  Constructors MUST NOT share an enum that either can't fully produce. `FromStr`'s error wraps it
  beside the syntax failure.
- Normalize first (trim, canonical case) so `Eq`/`Hash`/`Ord` compare canonical values, keeping
  every distinction the domain keeps (an email lowercases its domain, not its local part).
- No `Deref`/`DerefMut`, no `&mut` to the inner value: `as_str()`, `get()`, `AsRef`, `into_inner()`.
  A mutating method keeps the invariant or doesn't exist. `Default` only if the default is valid.
- serde: `#[serde(try_from = "String", into = "String")]` (or `"u16"`, …) via `TryFrom` and
  `From<Self> for Inner`. A derived `Deserialize`, `#[serde(transparent)]` or `#[sqlx(transparent)]`
  skips the constructor and MUST NOT be used; `Decode`/`FromSql` decodes the inner type, then
  `try_from`.
- clap: a refinement parses through `FromStr`, a closed set through `ValueEnum`; a custom
  `value_parser` needs a stated reason. `default_value_t = CONST` relies on the `Display`/`FromStr`
  round trip.
- Derive `Debug, Clone, PartialEq`, and `Copy`, `Eq`, `Hash`, `Ord` wherever the fields allow and
  the contract holds; `Borrow<str>` only if those agree with `str`'s. Hand-write a trait only where
  the derived behavior is wrong for the type (a redacted `Debug`, a `Default` that isn't the
  fields' defaults), never to spell out what the derive does, and then hand-write the traits that
  must agree with it (`Hash`, `PartialOrd`, `Ord` with `PartialEq`). Derived `Ord` follows
  declaration order: declare variants and fields in the domain's order; an order one caller needs
  is a `sort_by_key` there. `Eq` adds reflexivity (`a == a` for every value), which the compiler
  can't check: derive it (it compiles only when every field is `Eq`), and hand-write it only where
  the invariant guarantees it (a finite-float refinement rejects `NaN` and turns `-0.0` into `0.0`,
  so `Hash` and `Ord` agree with `==`), never over a `PartialEq` that breaks it (`f32`/`f64` aren't
  `Eq`: `NaN != NaN`). Where identity needs `Eq` and a field can't give it, fix the model (money:
  minor units or a decimal); a value meant to follow IEEE 754 keeps `PartialEq` alone.
- A secret hand-writes a redacted `Debug`, with no `Display` and no `Serialize`.
- `literal` calls `try_new`, never builds `Self`, and is `pub(crate)`; `pub` only when another crate
  needs the constants, then with a `# Panics` section.

## Errors

- Library errors are typed (`thiserror` enum, or a unit struct for one failure) and implement
  `Error + Send + Sync + 'static`, with typed context (`InvalidTransition { from, to }`); `String`,
  `&str`, `()` and `Box<dyn Error>` MUST NOT be the error or carry its context. `anyhow`/`eyre` only
  outside domain code (`main`, infrastructure), with `.context(…)`.
- A domain or library API MUST NOT return a dependency's error raw: wrap it in a variant of your
  own, kept as `#[source]`. An infrastructure adapter whose natural contract is std's error
  (`io::Result`) MAY return it.
- Derive `Clone, PartialEq, Eq` (reflexive, as above), and `Copy` where the fields allow, unless a
  cause can't (`io::Error`), so tests assert variants.
- Messages: lowercase, no trailing period, say what is wrong, never echo secret input.

## Behavior

- `unsafe` only where safe code can't do the job, and the crate says why (a measurement when the
  reason is speed): behind a safe API, in a module or crate of its own, never in domain code. A
  function is safe only if no argument causes undefined behavior; a condition only the caller can
  guarantee keeps it an `unsafe fn`, its contract under `# Safety`. A `// SAFETY:` comment states
  the invariant its block relies on.
- Functions are total: code MUST NOT panic on valid input or `assert!` on user input. `panic!`,
  `unwrap()`, `expect()` MUST NOT appear outside tests, except `expect()` with a clear message for
  `main.rs` bootstrap (the environment failing at startup: a config file, binding a port) under
  `#[expect(clippy::expect_used, reason = "…")]`. User input, CLI arguments included, is an error
  with a usage message and exit code, never `expect()`ed.
- A bug is neither an error variant nor a silent fallback (`unwrap_or_default()` over a state that
  can't happen): make the state unrepresentable; where types can't, a reasoned
  `#[expect(clippy::unreachable, …)]` marks the claim.
- Money: integer minor units or a decimal type, never `f32`/`f64`. Money and quantity arithmetic
  that can overflow uses `checked_*` and returns an error; check a possibly-zero divisor before `/`
  or `%`.
- Slice a `str` only at char boundaries (`split_once`, `char_indices`, `get(a..b)`), never
  `split_at`/`&s[a..b]` at an offset input can move. Input-dependent indexing MUST use
  `get`/`get_mut` and handle `None`, or check bounds first.
- Match your own enums exhaustively: no `_ =>`, no `#[non_exhaustive]` (it forces `_` arms on the
  workspace's other crates; only a crate published to users you don't rebuild uses it).
- Domain code: time and randomness are parameters, never ambient; output and decisions MUST NOT
  depend on `HashMap`/`HashSet` order (an ordered collection, or sort); no interior mutability
  (`&mut self`; the caller shares).
- Library code MUST NOT call `process::exit`/`abort`, `dbg!` or print macros; it returns errors and
  logs.
- No code runs before or after `main` (`#[ctor]`, `#[dtor]`): `main` starts and stops everything,
  in an order it shows, and handles the errors.
- A poisoned lock means a panic interrupted an update: its data is never read again
  (`PoisonError::into_inner`); the poisoning is an error.
- A name says what the thing does, never a catch-all (`Manager`, `Service`, `Utils`) or an abbreviation a
  newcomer wouldn't know; a single-letter lifetime or generic parameter only where one letter is
  unambiguous. Accessors follow std: `foo()`, `foo_mut()`, `set_foo()`, `take_foo()`,
  `replace_foo()`, never `get_foo()`.
- A trait exists only for a real abstraction need: a second implementation, a test double, outside
  implementors, a generic algorithm, or methods on a foreign type (an extension trait, named
  `…Ext`); never for flexibility nobody uses yet.
- An operator means its mathematical or logical operation (`Add` adds); anything else is a named
  method.
- Macros last: a function, type or trait; then `macro_rules!`; then a proc macro.
- Borrow inputs (`&str`, `&[T]`, `&T`, `Option<&T>`); own only to store, return or consume. No clone
  to quiet the borrow checker: shorten the borrow, move the value or change the API.
- Shared ownership (`Rc`/`Arc`) only where the lifetime really is shared (state that spawned tasks
  or handlers hold), never to escape a borrow; `Weak` breaks a cycle. A handle already shared
  inside (sqlx `Pool`, reqwest `Client`) is cloned, not wrapped in another `Arc`.

## Async

- A trait whose futures are spawned multithreaded returns `impl Future<Output = …> + Send`.
- No `std::sync::MutexGuard` across `.await`; no blocking on the runtime (`std::fs`, sync clients,
  heavy CPU): async APIs or `spawn_blocking`.
- Each `.await` can cancel. A future dropped there MUST NOT break a domain invariant or silently
  lose progress the application needs; where an operation can leave a partial effect (a partial
  write, a charge without its record), the caller preserves, recovers, compensates or explicitly
  accepts it.
- A future MUST be awaited, returned or spawned; a `JoinHandle` MUST be awaited or supervised, so
  its error and panic surface; detached work needs an owner and a failure path.

## Tests

- Per constructor: one accepted input, and every domain rejection reached by a test asserting its
  exact error (`assert_eq!(Port::try_new(0), Err(ZeroPort))`). No second example of a pinned rule;
  no tests of derives, getters or compiler guarantees.
- A law gets a property test instead of examples; where `Display` is the type's canonical text,
  a round-trip one MUST pin it: `prop_assert_eq!(v.to_string().parse(), Ok(v))` over generated
  values.
- Every forbidden transition the types allow is tested. `tests/` uses the public API.

## Lints

What clippy can check, clippy checks. Test allowances cover `#[test]` and `#[cfg(test)]`; a `tests/`
helper is neither (it returns `Result`, uses `?`). The lints hold: wildcard arms;
unwrap/expect/panic/todo/unimplemented/unreachable outside tests; unsafe, undocumented unsafe,
several unsafe operations per block and an `unsafe fn` without `# Safety`; a hand-written
`Default` a derive would produce; `Clone` on `Copy`; `Hash`/`Ord` derived beside a hand-written
`PartialEq`/`PartialOrd`; `#[ctor]`/`#[dtor]`;
public types missing `Debug`; `PartialEq` that could be `Eq`; infallible `TryFrom`; public
`Result<_, ()>`; never-failing `Result`; mixed `pub` fields; `Option<Option<T>>`; non-`Send`
futures; locks across `.await`; >3 bools; glob imports; `for_each`; needless pass by value;
`&Option` params; redundant clones; `map_err(|_| …)`; dropped `Result` or future;
`assert!(r.is_err())`; bare `#[allow]`, missing reasons; `anyhow`/`eyre`;
`Cell`/`RefCell`/`Mutex`/`RwLock`; banned clock/`rand`/`uuid` calls; `catch_unwind`; reading a
poisoned lock;
`process::abort`/`exit`; lossy `as`; `&s[a..b]` on `str`; hash `for` loops; debug and print macros.

Review every other rule, and what slips past a lint that looks like it holds:
- `new` returning `Result`; private type missing `Debug`; private `Result<_, ()>`;
  `map_err(|e| e.to_string())` (names the cause, loses its type); `.ok()` hiding an error.
- `Result`/future bound to `_name` or `drop`ped; `split_at` on `str`; overflowing arithmetic; hash
  iterator chains (`map.keys().collect()`) whose order matters.
- Time or randomness missing from `clippy.toml`; atomics, `OnceCell`, other interior mutability in
  domain code.
- Unused dependencies; a rejection test asserting its error in a form the lint misses, not exactly.
- An unambiguous conversion or complete text parse without its trait: such text parsed by
  anything but `FromStr` (`TryFrom<&str>`/`<String>` alone included), or a named function in the
  trait's place whose doc comment doesn't say what the trait would hide (`should_implement_trait`
  only sees a method named `from_str`).

## Allowed

Not defects, not even nits:
- A tag's `pub` field, `#[serde(transparent)]`, and `From` where the types make the meaning obvious.
- `Result<Option<T>, E>` from a lookup; `Option` from a function that can't fail.
- A unit-struct error for a constructor with one failure.
- An extension trait (`…Ext`) with a single implementation, on a foreign type.
- Instead of `try_new`: an I/O resource's fallible `open`/`connect`/`bind`, a fallible `with_*`,
  and a `from_*` that chooses or that sits beside the trait a conversion requires.
- An error lacking `Clone`/`PartialEq`/`Eq` because a cause does (`io::Error`).
- `#[non_exhaustive]` in a crate published to users you don't rebuild.
- `literal`'s panic in `const` items, under its `#[expect]`.
- `main.rs` `expect()` with a clear message for an environment startup failure, under its
  `#[expect]`.
- `unwrap()`, `expect()`, `panic!` in `#[test]` and `#[cfg(test)]` code.
- `anyhow`/`eyre`, the clock, randomness and locks outside domain code, where clippy.toml's comments
  exempt them.
- A non-`Send` future deliberately run only on a local executor, with a reasoned
  `#[expect(clippy::future_not_send, reason = "…")]`.
- A `Result` dropped where dropping is right (a send whose receiver may be gone), under a reasoned
  `#[expect(clippy::let_underscore_must_use, reason = "…")]`.
- A named parser or decoder for a parse that extracts or chooses, beside the type's `FromStr` where
  complete text has one interpretation.

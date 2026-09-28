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

## Precedence

These guidelines MUST override default Rust conventions in the project you are working on. If following them creates
an important technical conflict, raise it during planning. ADRs MAY override these patterns when explicitly recorded.
Interpret `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, and `MAY` literally.

## Philosophy

Use Rust's type system, ownership model, and enums as architecture, not just syntax to enforce discipline that other languages simulate with patterns.

Two axioms drive the type-level decisions:

1. **If it compiles, it's valid.** Encode rules in types so invalid states CANNOT exist.
2. **Ownership is design.** Who owns a value, who borrows it, and who consumes it are not
   implementation details — they shape the API.

- The standard library SHOULD be preferred over new dependencies unless a crate provides clear value.
- `unsafe` MUST be minimized; every unsafe block MUST document its invariants.

---

## Parse, Don't Validate

All external data is untrusted. It is parsed once, at the edge where it enters, into a domain
type, and from then on the type is the proof: HTTP and RPC handlers, the CLI, config load,
database decode, queue consumers, files, and environment variables.

Rules:

- External data MUST be parsed at the edge and trusted afterward. Code MUST NOT re-check an
  invariant after successful parsing.
- Domain functions MUST take the domain type (`Email`), never the primitive it was parsed from
  (`&str`).
- A check that answers yes or no, such as `is_valid_x(&str) -> bool` or `validate(&self)` over
  public fields, MUST be replaced by a constructor that returns the type.
- Inbound conversions SHOULD use `TryFrom` / `TryInto`, or `FromStr` for text. Outbound
  conversions SHOULD use `From` / `Into`.
- Every way in (serde, clap, a database decode, `FromStr`, `TryFrom`) MUST reach a refinement
  through its one validating constructor (Newtypes). A derive that builds the value field by
  field skips it: a derived `Deserialize`, `#[serde(transparent)]`, `#[sqlx(transparent)]`, or a
  `Default` whose value breaks the invariant. Deserialize a record or DTO and convert it with
  `TryFrom`, or route the derive through the constructor with `#[serde(try_from = "…")]`. A
  fieldless enum MAY derive `Deserialize`: every value it can hold is valid.
- Domain code SHOULD live under a `domain` path (a `domain/` module, or a crate whose path
  contains `domain`), and records and DTOs elsewhere, so a tool can tell them apart.

```rust
#[derive(Deserialize)]
pub struct CreateOrderRequest {
    pub customer_id: String,
    pub items: Vec<OrderItemDto>,
}

impl TryFrom<CreateOrderRequest> for CreateOrder {
    type Error = ValidationError;

    fn try_from(req: CreateOrderRequest) -> Result<Self, Self::Error> {
        Ok(CreateOrder {
            customer: req.customer_id.parse()?, // CustomerId: FromStr, its one canonical text form
            items: req.items
                .into_iter()
                .map(OrderItem::try_from)
                .collect::<Result<Vec<_>, _>>()?,
        })
    }
}
```

---

## Type-Driven Design

### Core rules

- Illegal states MUST be unrepresentable. Structure comes before a runtime check, and before
  a newtype:
  - States that exclude each other MUST be one enum, not several `bool` flags, `Option`s, or a
    string.
  - Fields that exist only together MUST be one variant's data, not co-dependent `Option`s.
  - A collection that cannot be empty SHOULD be `NonEmpty<T>` (or a head plus a `Vec`), not a
    `Vec` plus a length check; a number that cannot be zero SHOULD be `NonZero*`.
  - Typestate SHOULD be used when the risk is calling operations in the wrong order, and only
    when the state is known statically at every call site and invalid transitions are costly.
    State read from storage or the wire MUST be an enum, since its value is known only at
    runtime.
- A value SHOULD get a newtype when it carries an invariant, or when it could be swapped with
  another value of the same primitive (`StoreName` / `StoreAddress`). A value with neither
  SHOULD NOT be wrapped.
- Every newtype is one of two kinds, and its field says which:
  - A **tag** (`UserId(u64)`) has no invariant; it exists only to prevent mix-ups. Its field is
    `pub`, and `From` and `#[serde(transparent)]` are fine. architecture-blueprint calls it an
    identity newtype.
  - A **refinement** (`Email`, `Port`) has an invariant. Its fields MUST be private, and every
    rule under Newtypes applies. architecture-blueprint calls a single-value refinement a value
    object.

  A private field declares a refinement: that is how the tools below tell the two apart.
- Enum variant fields are always public. A variant whose fields share an invariant
  (`sale < regular`) MUST wrap a private-field struct instead of carrying the fields itself.
- Absence MUST be an `Option` with one stated meaning, or a variant. Sentinels (`""`, `0`,
  `-1`) MUST NOT stand for absence. When `None` would mean two things, use an enum.
- Enums + structs SHOULD be preferred over class hierarchies.
- State transitions SHOULD default to immutable values.

### Newtypes

A refinement's rules. Read [references/newtypes.md](references/newtypes.md) when adding or
reviewing one: it holds the error, serde, clap, database and std trait rules, and a complete
template, checked against this skill's own tools.

Pick the constructor by its input:

| Input | Provide |
| --- | --- |
| One canonical text form | `FromStr`, plus `Display` as its exact inverse |
| An owned `String` the value keeps | `TryFrom<String>` as well as `FromStr`, so it is not copied |
| One non-string source with an obvious mapping | `TryFrom<u16>` (and so on) |
| Several arguments, or a name adds meaning | an inherent `fn new(a, b) -> Result<Self, E>` |
| Several formats | named constructors: `from_hex`, `from_rgb`, `from_secs` |
| Needs context, or consumes part of the input | `fn parse(input, &ctx)`, or a parser returning `(T, &rest)` |
| A DTO, row or payload | `impl TryFrom<Dto> for Domain` |
| Every input is valid | `From`, never `TryFrom` |
| A compile-time literal | `const fn literal(..) -> Self` that panics, called only in `const` items |
| Zero-copy, borrowed | `TryFrom<&'a str> for Name<'a>` (`FromStr` cannot borrow) |
| A trusted internal source | `pub(crate) fn from_trusted`; `unsafe fn new_unchecked` only if soundness depends on the invariant |

Naming:

- The sole fallible constructor MUST be named `new` and return `Result` or `Option`, as std does
  (`NonZero::new`, `CString::new`).
- `try_new` MUST exist only beside an infallible or panicking `new` (`Box::new` / `Box::try_new`).
- A constructor MUST return `Option` only for one self-evident failure (zero, empty); any other
  returns `Result` with a dedicated error enum.
- An inherent `parse(&str)` MAY exist for discoverability; it MUST delegate to the same path as
  `FromStr`.

Invariant integrity:

- A refinement MUST have one validating function. `FromStr`, `TryFrom`, serde, clap and database
  decoding all delegate to it.
- Its fields MUST stay private: the module is the trust boundary. It MUST NOT hand out `&mut` to
  its inner value, nor implement `Deref` or `DerefMut`; it offers `as_str()`, `get()`, `AsRef` or
  `into_inner()` instead.
- The constructor MUST normalize to the canonical form the domain defines (trim, canonical
  case), so `Eq`, `Hash` and `Ord` compare canonical values; it never collapses a distinction the
  domain keeps (an email's local part keeps its case).
- A mutating method MUST preserve the invariant, or not exist (`NonEmptyVec::pop` returns `None`
  at length 1).
- A refinement SHOULD build on std's (`Port(NonZeroU16)`, not `Port(u16)` plus a check), which
  also gives a niche: `Option<Port>` is 2 bytes.
- It MUST NOT derive `Default` unless the default value is valid.

```rust
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Email(String);

// The field is private, so new() is the only way in; FromStr (below), TryFrom<String> and serde
// (references/newtypes.md) delegate to it. After new() succeeds, the Email is trusted everywhere.
impl Email {
    pub fn new(raw: impl Into<String>) -> Result<Self, EmailError> {
        let raw = raw.into();
        // Normalized first; an already trimmed String is kept, not copied.
        let value = if raw.trim().len() == raw.len() {
            raw
        } else {
            raw.trim().to_owned()
        };
        if value.is_empty() {
            return Err(EmailError::Empty);
        }
        if !value.contains('@') {
            return Err(EmailError::MissingAt);
        }
        Ok(Self(value))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl FromStr for Email {
    type Err = EmailError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        Self::new(s)
    }
}

// One self-evident failure, so Option; std's NonZeroU16 holds the invariant.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Port(NonZeroU16);

impl Port {
    pub const fn new(n: u16) -> Option<Self> {
        match NonZeroU16::new(n) {
            Some(n) => Some(Self(n)),
            None => None,
        }
    }
}
```

### Illegal states

```rust
enum Shipment {
    Pending { order_id: OrderId },
    Shipped { order_id: OrderId, tracking: TrackingNumber },
    Delivered { order_id: OrderId, tracking: TrackingNumber, delivered_at: DateTime<Utc> },
    Cancelled { order_id: OrderId, reason: CancellationReason },
}

// A cross-field invariant lives in a private-field struct, never in variant fields,
// or `Price::Cut { sale: high, regular: low }` could be built by a struct literal.
pub enum Price {
    Regular(Money),
    Cut(PriceCut),
}

pub struct PriceCut {
    sale: Money,
    regular: Money,
}

impl PriceCut {
    pub fn new(sale: Money, regular: Money) -> Result<Self, PriceError> {
        if sale < regular {
            Ok(Self { sale, regular })
        } else {
            Err(PriceError::NotACut { sale, regular })
        }
    }
}
```

### Partial updates

Partial updates SHOULD be modeled as `Option` fields whose present values are already parsed domain types.

```rust
pub struct OrderUpdate {
    pub new_status: Option<OrderStatus>,
    pub shipping: Option<ShippingAddress>,
}

impl Order {
    pub fn apply(self, update: OrderUpdate) -> Result<Self, OrderError> {
        let status = match update.new_status {
            Some(next) => self.status.transition_to(next)?,
            None => self.status,
        };
        let shipping = update.shipping.unwrap_or(self.shipping);

        Ok(Self { status, shipping, ..self })
    }
}
```

---

## Error Modeling

Errors are typed and structured, never stringly typed.

```rust
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum OrderError {
    #[error("cannot transition from {from} to {to}")]
    InvalidTransition { from: OrderStatus, to: OrderStatus },
    #[error("order total exceeds credit limit: {total} > {limit}")]
    CreditLimitExceeded { total: Money, limit: Money },
    #[error("empty order")]
    EmptyOrder,
}

// The adapter translates its infrastructure error at the boundary and keeps it as the cause.
// io::Error is neither Clone nor PartialEq, so this error derives neither; tests use matches!.
#[derive(Debug, thiserror::Error)]
pub enum LoadError {
    #[error("order {id} not found")]
    NotFound { id: OrderId },
    #[error("order store unavailable")]
    StoreUnavailable(#[source] std::io::Error),
}
```

Rules:

- Error variants MUST carry typed context, not ad-hoc strings.
- Library code MUST return typed errors: an error type implements
  `std::error::Error + Send + Sync + 'static`, which clap, anyhow and `Box<dyn Error>` require.
  `String` and `()` MUST NOT be error types.
- An error SHOULD derive `Debug, Clone, PartialEq, Eq`, so tests assert on variants, unless it
  holds a cause that cannot (`io::Error`).
- A message MUST be lowercase, with no trailing period, and state what is wrong
  (`"port must be non-zero"`): it is read inside a longer chain. An acronym or a name keeps its
  case. A message MUST NOT echo secret input.
- A public library's error enums SHOULD be `#[non_exhaustive]`.
- Errors SHOULD compose through explicit `From` impls so `?` stays honest.
- An infrastructure error MUST NOT cross a domain or capability boundary raw: translate it into
  the caller's error type there, and keep the original as `#[source]` so the chain survives.
- Libraries SHOULD use `thiserror`; `anyhow` / `eyre` SHOULD be limited to process boundaries.
- Application code using `anyhow` SHOULD add `.context(...)` when propagating fallible operations.
- Code MUST NOT use `Err("something went wrong".into())`.

---

## Invariants and Assertions

Enforce invariants in this order:

1. Encode the invariant in a type.
2. Return a typed error.
3. Use `debug_assert!()` for impossible states that indicate a bug.
4. Use `assert!()` only when continuing would be unsafe or corrupt state.

Rules:

- User input MUST NOT be validated with assertions.
- Exhaustive `match` SHOULD be preferred over `unreachable!()`.
- An invariant that can live in a type MUST be checked once, in its constructor, and never
  re-checked downstream.

```rust
impl Order {
    // Non-empty items are held by the type that built this Order; only the rule
    // that depends on two values is checked here.
    pub fn confirm(self) -> Result<ConfirmedOrder, OrderError> {
        if self.total > self.credit_limit {
            return Err(OrderError::CreditLimitExceeded {
                total: self.total,
                limit: self.credit_limit,
            });
        }
        Ok(ConfirmedOrder { /* ... */ })
    }
}
```

---

## Behavior Rules

- Functions SHOULD be total. Code MUST NOT panic on valid input.
- Code MUST match exhaustively on its own enums: no wildcard `_ =>` arm, so adding a variant
  breaks the build everywhere it matters.
- `Result` / `Option` combinators SHOULD be used when they clarify the flow; pipelines SHOULD NOT be forced where straight-line code is clearer.
- Functions SHOULD borrow inputs when ownership is not required.
- A constructor that keeps its input SHOULD accept it owned-friendly (`impl Into<String>`, and
  `TryFrom<String>` beside `FromStr`), so a caller holding a `String` hands it over without a copy;
  one that only reads its input, parsing it into other fields, SHOULD take `&str`. Either returns
  an owned value.
- Important return values SHOULD use `#[must_use]` when ignoring them is likely a bug.
- Time and randomness SHOULD be parameters, not ambient calls (`Utc::now()`, `rand`) inside
  domain logic. That is what keeps domain tests deterministic.
- Generic role names like `Service`, `Manager`, `Helper`, `Utils`, and `Misc` MUST NOT be introduced (checked by ast-grep under Enforce with Tools).

### Mutation discipline

- APIs SHOULD default to immutable interfaces.
- `&mut self` SHOULD be used when it is the natural model, improves performance, or avoids unnecessary allocation.
- Domain types MUST NOT use interior mutability (`Cell`, `RefCell`, `Mutex`).

### Allocation discipline

- Owned types SHOULD be the default.
- Borrowed types SHOULD be used for transient parsing and short-lived views.
- Struct lifetimes SHOULD NOT be introduced unless profiling shows a measurable need.
- Code SHOULD prefer borrowing over cloning when ownership does not need to change.
- `clone()` SHOULD NOT appear inside per-item loops or other hot paths without a stated reason.

---

## Dependency Injection

- Traits SHOULD define capabilities: `LoadOrders`, `ChargePayment`, `PublishEvent`.
- Callers SHOULD depend on capabilities; adapters SHOULD implement them at the edges.
- A trait SHOULD NOT be introduced for a single implementation unless a real second implementation or test double is needed.
- Traits with `async fn` are not dyn-compatible, and their futures are not promised `Send`.
  When a trait's futures are spawned onto a multithreaded runtime, the method MUST declare
  `-> impl Future<Output = …> + Send`; implementors may still write `async fn`.
- Generics or a closed `enum` over the implementations SHOULD be preferred to `dyn`.

```rust
pub trait LoadOrders {
    fn load(&self, id: &OrderId) -> impl Future<Output = Result<Order, LoadError>> + Send;
}
```

### When to introduce a trait

| Situation                                          | Use a trait? |
|----------------------------------------------------|--------------|
| 2+ real implementations                            | Yes          |
| 1 real impl but need test doubles for side effects | Yes          |
| Pure function with no side effects                 | No           |
| Single impl, easily testable directly              | No           |

---

## Async / Runtime Rules

### Task boundaries

- Values moved into spawned tasks MUST satisfy runtime bounds such as `Send + 'static`.
- Code MUST move owned data into tasks and MUST NOT borrow across task boundaries.
- `Arc<T>` + immutable state SHOULD be preferred. Shared mutation MUST be explicitly justified.
- `std::sync::MutexGuard` MUST NOT be held across `.await`.
- `tokio::sync::Mutex` SHOULD be used only when a lock truly must span `.await`.

### Cancellation

- Every `await` MUST be treated as a cancellation point.
- Workflows with money, inventory, or external side effects MUST be idempotent or transactionally safe.

### Blocking work

- Async code MUST NOT block the runtime.
- Blocking I/O or CPU-heavy work MUST use async-aware APIs or `spawn_blocking`.

### Panic policy

- `panic!`, `unwrap()`, and `expect()` MUST NOT appear in production paths.
- They MAY be used in tests and unrecoverable bootstrap code in `main.rs` with a clear message.
- A `const fn literal` (Newtypes) MAY panic, and is called only in a `const` item, where an
  invalid value fails compilation instead of a run. It carries
  `#[expect(clippy::panic, reason = "a compile-time literal: an invalid value fails compilation")]`.

---

## Testing Strategy

- Unit tests for pure domain logic SHOULD be the default: fast, deterministic, no mocks.
- Integration tests SHOULD live in `tests/` and exercise the public API only.
- Cancellation tests SHOULD be added for async workflows with externally visible side effects.

### Budget

- Each constructor gets one accepted input and one rejected input, plus one rejected input per
  distinct *reason* for rejection. More examples of a rule already pinned SHOULD NOT be added.
- Where a law exists (round-trip, idempotence, a charset), a property test SHOULD replace the
  examples.
- A type with both `Display` and `FromStr` MUST have a property test that its `Display` parses
  back: `Display` is `FromStr`'s exact inverse, and clap's `default_value_t` relies on it.
- State transitions SHOULD be tested for each forbidden transition the type cannot rule out.
- Every rejection in domain code MUST be reached by a test; rejection coverage (Enforce with
  Tools) checks it.

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pending_order_can_transition_to_confirmed() {
        let order = Order::pending(customer_id(), items());
        let confirmed = order.confirm().unwrap();
        assert!(matches!(confirmed.status(), OrderStatus::Confirmed));
    }
}
```

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn port_display_parses_back(n in 1u16..) {
        let port = Port::try_from(n)?;
        prop_assert_eq!(port.to_string().parse::<Port>(), Ok(port));
    }
}
```

### What not to test

- Private helpers SHOULD be tested through the public API.
- Framework glue SHOULD NOT be tested unless custom logic is involved.
- Tests SHOULD NOT target what the compiler already guarantees, nor derives, getters, or a
  `Display` with no `FromStr` to invert.

---

## Enforce with Tools

A rule a deterministic tool can check (the compiler, clippy, rustfmt, a grep in CI) MUST be checked
by that tool, not by an agent's or a reviewer's reading. Review covers only what no tool can decide.
A tool is repeatable and cannot be talked out of a verdict; a reading is neither.

```toml
# Cargo.toml — each lint names what it catches, then the rule it holds and where that rule lives above.
[lints.rust]
# Any `unsafe` at all. Philosophy: unsafe minimized. `forbid` cannot be lifted in code: a crate that
# truly needs unsafe sets this to "deny" and puts #[expect(unsafe_code, reason = "…")] on each item.
unsafe_code = "forbid"
# A public type without Debug. references/newtypes.md, std traits: every newtype and every error provides Debug.
missing_debug_implementations = "deny"

[lints.clippy]
# A type deriving PartialEq that could derive Eq. references/newtypes.md, std traits, and Error Modeling: Eq wherever it holds.
derive_partial_eq_without_eq = "deny"
# `.unwrap()` outside tests. Panic policy: no unwrap in production paths; Behavior Rules: functions are total.
unwrap_used = "deny"
# `.expect()` outside tests. Panic policy: no expect in production paths.
expect_used = "deny"
# `panic!` outside tests. Panic policy: no panic in production paths; Behavior Rules: no panic on valid input.
panic = "deny"
# `todo!()`, a placeholder that panics. Behavior Rules: functions are total.
todo = "deny"
# `unimplemented!()`, a placeholder that panics. Behavior Rules: functions are total.
unimplemented = "deny"
# `unreachable!()`. Invariants and Assertions: prefer an exhaustive match, which the compiler checks.
unreachable = "deny"
# `_ =>` over several variants of your own enum. Behavior Rules: match exhaustively, so a new variant breaks the build.
wildcard_enum_match_arm = "deny"
# `_ =>` standing for a single variant, which the lint above skips. Same rule.
match_wildcard_for_single_variants = "deny"
# A std `MutexGuard` held across `.await`. Async, task boundaries: never hold one across an await.
await_holding_lock = "deny"
# A `RefCell` borrow held across `.await`. Async, task boundaries: the same hazard, and Mutation discipline.
await_holding_refcell_ref = "deny"
# A future that is not `Send`. Dependency Injection and task boundaries: a future spawned multithreaded must be Send.
future_not_send = "deny"
# A parameter taken by value but never consumed. Behavior Rules: borrow inputs when ownership is not required.
needless_pass_by_value = "deny"
# A clone whose original is never used again. Allocation discipline: borrow rather than clone when ownership stays.
redundant_clone = "deny"
# A struct with more than three bools. Type-Driven Design: exclusive states are one enum, not bool flags.
struct_excessive_bools = "deny"
# A function with more than three bool parameters. Same rule, at the call site.
fn_params_excessive_bools = "deny"
# The types clippy.toml bans. Error Modeling (no anyhow or eyre in libraries); Mutation discipline (no interior mutability).
disallowed_types = "deny"
# The functions clippy.toml bans. Behavior Rules: time and randomness are parameters in domain logic.
disallowed_methods = "deny"
# An `unsafe` block without a `// SAFETY:` comment. Philosophy: every unsafe block documents its invariants.
undocumented_unsafe_blocks = "deny"
# A bare `#[allow]`. Enforce with Tools: silence with `#[expect]`, which fails once the lint no longer fires.
allow_attributes = "deny"
# A silencing attribute with no `reason`. Enforce with Tools: a tool's verdict is never waved away without saying why.
allow_attributes_without_reason = "deny"
```

```toml
# clippy.toml, in each crate's root (a crate without one inherits the workspace's)
# Panic policy: unwrap, expect and panic MAY appear in tests.
allow-unwrap-in-tests = true
allow-expect-in-tests = true
allow-panic-in-tests = true
disallowed-types = [
  # Error Modeling: libraries return typed errors; anyhow and eyre stay at process boundaries.
  # Library and domain crates only; a binary crate's own clippy.toml leaves these two out.
  { path = "anyhow::Error", reason = "library code returns typed errors", allow-invalid = true },
  { path = "eyre::Report", reason = "library code returns typed errors", allow-invalid = true },
  # Mutation discipline: domain types hold no interior mutability. Domain crates only.
  { path = "std::cell::Cell", reason = "domain types hold no interior mutability" },
  { path = "std::cell::RefCell", reason = "domain types hold no interior mutability" },
  { path = "std::sync::Mutex", reason = "domain types hold no interior mutability" },
]
disallowed-methods = [
  # Behavior Rules: time and randomness are parameters, which keeps domain tests deterministic. Domain crates only.
  { path = "std::time::SystemTime::now", reason = "pass the time in" },
  { path = "std::time::Instant::now", reason = "pass the time in" },
  { path = "chrono::Utc::now", reason = "pass the time in", allow-invalid = true },
  { path = "rand::random", reason = "pass the source of randomness in", allow-invalid = true },
  { path = "rand::thread_rng", reason = "pass the source of randomness in", allow-invalid = true },
]
```

`allow-invalid` keeps an entry quiet in a crate that does not depend on that library.

The test allowances cover `#[cfg(test)]` code only. Each file under `tests/` is its own crate,
so the denies apply there in full: integration tests SHOULD return `Result<(), Box<dyn Error>>`
and use `?`.

A lint that misfires is silenced where it misfires, with `#[expect(clippy::name, reason = "…")]`,
never switched off for the crate.

### Syntax rules: ast-grep

What clippy cannot see, a syntax pattern can: attributes on a type, the shape of an error value, a
type's name. [ast-grep](https://ast-grep.github.io) (`cargo install ast-grep --locked`; these rules
were verified on 0.45.3) matches the syntax tree, so a comment or a string that mentions a name
never counts. `ast-grep scan` exits non-zero on any finding.

```yaml
# sgconfig.yml, at the repository root
ruleDirs:
  - .ast-grep/rules
utilDirs:  # patterns several rules share
  - .ast-grep/utils
```

```yaml
# .ast-grep/utils/attributes-before.yml
# Where a search up through an item's attributes stops: the first node above that is neither an attribute nor a comment.
id: attributes-before
language: rust
rule:
  not: { any: [{ kind: attribute_item }, { kind: line_comment }, { kind: block_comment }] }
```

```yaml
# .ast-grep/utils/refinement.yml
# A refinement: a struct with a private field. A tag's field is pub (Type-Driven Design).
id: refinement
language: rust
rule:
  kind: struct_item
  has:
    field: body
    any:
      - kind: field_declaration_list
        has: { kind: field_declaration, not: { has: { kind: visibility_modifier } } }
      - kind: ordered_field_declaration_list
        has:  # a field type whose previous token is not `pub`; punctuation tokens are children here too
          not: { any: [{ kind: visibility_modifier }, { kind: attribute_item }, { kind: line_comment }, { kind: block_comment }, { regex: '^[(),]$' }] }
          follows: { not: { kind: visibility_modifier } }
```

```yaml
# .ast-grep/rules/refinement-bypass.yml
# A refinement (a domain struct with a private field) that serde or sqlx builds field by field, skipping its constructor.
# Holds Parse, Don't Validate: "Every way in MUST reach a refinement through its one validating constructor".
id: refinement-bypass
language: rust
severity: error
message: A derive builds this refinement without its constructor.
note: "Parse, Don't Validate: route serde through #[serde(try_from = \"...\")], and decode from the database through TryFrom."
files: ["**/domain/**"]  # the domain path convention above; records and DTOs live elsewhere
rule:
  all:
    - matches: refinement
    - any:
        - all:
            - follows: { kind: attribute_item, regex: 'derive\([^)]*\bDeserialize\b', stopBy: { matches: attributes-before } }
            - not:  # try_from runs the constructor; from, an infallible From, has nothing to skip
                follows: { kind: attribute_item, regex: 'serde\([^)]*\b(try_)?from\s*=', stopBy: { matches: attributes-before } }
        - follows: { kind: attribute_item, regex: '^#\[(serde|sqlx)\([^)]*\btransparent\b', stopBy: { matches: attributes-before } }
```

```yaml
# .ast-grep/rules/refinement-default.yml
# A refinement deriving Default, whose value no constructor checked.
# Holds Newtypes: "It MUST NOT derive Default unless the default value is valid".
id: refinement-default
language: rust
severity: error
message: A refinement derives Default.
note: "Newtypes: remove the derive; when the default is valid, say why directly above `pub struct`, below its attributes: // ast-grep-ignore: refinement-default -- <why>"
files: ["**/domain/**"]
rule:
  all:
    - matches: refinement
    - follows: { kind: attribute_item, regex: 'derive\([^)]*\bDefault\b', stopBy: { matches: attributes-before } }
```

```yaml
# .ast-grep/rules/stringly-typed-error.yml
# A string where an error should be: a literal or format! in Err, or String as a Result's error type.
# Holds Error Modeling: "Code MUST NOT use Err("something went wrong".into())"; variants carry typed context.
id: stringly-typed-error
language: rust
severity: error
message: A stringly typed error.
note: "Error Modeling: errors are typed variants with typed context, never ad-hoc strings."
ignores: ["tests/**"]
rule:
  any:
    - pattern: Err($S.into())
    - pattern: Err($S.to_string())
    - pattern: Err($S.to_owned())
    - pattern: Err(String::from($S))
    - pattern: Err(format!($$$))
    - pattern: { context: 'type T = Result<$A, String>;', selector: generic_type }
constraints:
  S: { kind: string_literal }  # Err(value.into()) converting a typed value stays legal
```

```yaml
# .ast-grep/rules/infra-error-without-source.yml
# An enum variant holding an infrastructure error with neither #[source] nor #[from], which drops the cause chain.
# Holds Error Modeling: "keep the original as #[source] so the chain survives".
id: infra-error-without-source
language: rust
severity: error
message: An infrastructure error is held without #[source] or #[from], so its chain is lost.
note: "Error Modeling: translate it at the boundary and keep the original as #[source]."
utils:
  infra-error:  # the project's adapters: extend this list with its own
    any: [{ kind: scoped_type_identifier }, { kind: type_identifier }]
    regex: '^((std::)?io::Error|sqlx::Error|reqwest::Error|serde_json::Error)$'
  source-attribute:
    kind: attribute_item
    regex: '^#\[(source|from)\]$'
rule:
  all:
    - matches: infra-error
    - inside: { kind: enum_variant, stopBy: end }
    - not:
        any:
          - follows: { matches: source-attribute }  # tuple variant: (#[source] io::Error)
          - inside:  # struct variant: { #[source] err: io::Error }, or thiserror's implicit `source` field
              kind: field_declaration
              any:
                - follows: { matches: source-attribute }
                - has: { field: name, regex: '^source$' }
```

```yaml
# .ast-grep/rules/generic-role-name.yml
# A type named for a role instead of what it is.
# Holds Behavior Rules: "Generic role names like Service, Manager, Helper, Utils, and Misc MUST NOT be introduced".
id: generic-role-name
language: rust
severity: error
message: A generic role name says what a type is for, not what it is.
note: "Behavior Rules: name the capability (LoadOrders, ChargePayment), not a role."
rule:
  kind: type_identifier
  regex: '(Service|Manager|Helper|Utils|Misc)$'
  inside:  # the name being declared, never a use of one
    any: [{ kind: struct_item }, { kind: enum_item }, { kind: trait_item }, { kind: type_item }]
    field: name
```

```yaml
# .ast-grep/rules/newtype-derives.yml
# A domain newtype (a tuple struct of one field) that does not derive Clone, PartialEq, Eq and Hash.
# Holds references/newtypes.md, std traits: "Every newtype provides Debug, Clone, PartialEq, Eq, Hash" (Debug is rustc's lint).
id: newtype-derives
language: rust
severity: error
message: A newtype without Clone, PartialEq, Eq and Hash.
note: "references/newtypes.md: derive them; a type that cannot (an f64 inside) says why directly above `pub struct`, below its attributes: // ast-grep-ignore: newtype-derives -- <why>"
files: ["**/domain/**"]
rule:
  all:
    - kind: struct_item
    - has:  # one field: no comma before another field
        field: body
        kind: ordered_field_declaration_list
        not: { has: { regex: '^,$', not: { precedes: { regex: '^\)$' } } } }
    - any:
        - not: { follows: { kind: attribute_item, regex: 'derive\([^)]*\bClone\b', stopBy: { matches: attributes-before } } }
        - not: { follows: { kind: attribute_item, regex: 'derive\([^)]*\bPartialEq\b', stopBy: { matches: attributes-before } } }
        - not: { follows: { kind: attribute_item, regex: 'derive\([^)]*\bEq\b', stopBy: { matches: attributes-before } } }
        - not: { follows: { kind: attribute_item, regex: 'derive\([^)]*\bHash\b', stopBy: { matches: attributes-before } } }
```

```yaml
# .ast-grep/rules/validation-predicate.yml
# A check that answers yes or no instead of returning the parsed type.
# Holds Parse, Don't Validate: "is_valid_x(&str) -> bool or validate(&self) MUST be replaced by a constructor that returns the type".
id: validation-predicate
language: rust
severity: error
message: A validation that returns a verdict, not the type.
note: "Parse, Don't Validate: a constructor that returns the type (Newtypes) replaces it, and the type is the proof."
ignores: ["tests/**"]
rule:
  kind: function_item
  all:
    - has: { field: name, regex: '^(validate|is_valid)(_\w+)?$' }
    - has: { field: return_type, regex: '^(bool|(\w+::)*Result<\s*\(\s*\)\s*[,>])' }  # bool, or Result<(), _>
```

```yaml
# .ast-grep/rules/infallible-try-from.yml
# A TryFrom impl that cannot fail.
# Holds Newtypes: "Every input is valid: From, never TryFrom".
id: infallible-try-from
language: rust
severity: error
message: A TryFrom whose Error is Infallible.
note: "Newtypes: every input is valid, so implement From; TryFrom comes with it for free."
rule:
  kind: impl_item
  all:
    - has: { field: trait, regex: '^((std|core)::convert::)?TryFrom\b' }
    - has: { field: body, has: { kind: type_item, regex: '^type\s+Error\s*=\s*((std|core)::convert::)?Infallible\s*;' } }
```

```yaml
# .ast-grep/rules/try-new-without-new.yml
# A try_new with no infallible or panicking new beside it in the same impl.
# Holds Newtypes: "try_new MUST exist only beside an infallible or panicking new".
id: try-new-without-new
language: rust
severity: error
message: try_new without an infallible new beside it.
note: "Newtypes: the sole fallible constructor is new; try_new is the fallible twin of a new that cannot fail (Box::new, Box::try_new)."
ignores: ["tests/**"]
rule:
  kind: function_item
  has: { field: name, regex: '^try_new$' }
  inside:
    kind: declaration_list
    not:
      has:
        kind: function_item
        all:
          - has: { field: name, regex: '^new$' }
          - not: { has: { field: return_type, regex: '^((\w+::)*Result|Option)\b' } }
```

```yaml
# .ast-grep/rules/literal-outside-const.yml
# A panicking literal constructor called where it runs at runtime.
# Holds the Panic policy: "A const fn literal is called only in a const item, where an invalid value fails compilation".
id: literal-outside-const
language: rust
severity: error
message: A literal constructor called outside a const item, where a bad value panics at runtime.
note: "Panic policy: bind it to a const item (pub const HTTP: Port = Port::literal(80)), or call the fallible new."
ignores: ["tests/**"]
rule:
  pattern: $T::literal($$$)
  not: { inside: { any: [{ kind: const_item }, { kind: static_item }, { kind: const_block }], stopBy: end } }
```

```yaml
# .ast-grep/rules/error-message-style.yml
# An error message that starts with a capitalized word (a single letter too, as in "A port") or ends with a period.
# Holds Error Modeling: "A message MUST be lowercase, with no trailing period"; an acronym (HTTP, I/O) keeps its case.
id: error-message-style
language: rust
severity: error
message: An error message that starts with a capital or ends with a period.
note: "Error Modeling: it is read inside a longer chain; a name keeps its case, silenced on the line above: // ast-grep-ignore: error-message-style -- <the name>"
rule:
  kind: attribute_item
  regex: '^#\[error\("([A-Z][a-z]|[A-Z]\s|[^"]*\.")'
```

```yaml
# .ast-grep/rules/domain-error-derives.yml
# A domain error that tests cannot compare: it derives Error without Clone and PartialEq, and holds no cause.
# Holds Error Modeling: "An error SHOULD derive Debug, Clone, PartialEq, Eq ... unless it holds a cause that cannot".
id: domain-error-derives
language: rust
severity: error
message: A domain error without Clone and PartialEq.
note: "Error Modeling: derive Debug, Clone, PartialEq, Eq, so tests assert on variants; an error that cannot says why directly above `pub enum`, below its attributes: // ast-grep-ignore: domain-error-derives -- <why>"
files: ["**/domain/**"]
rule:
  all:
    - kind: enum_item
    - follows: { kind: attribute_item, regex: 'derive\([^)]*\bError\b', stopBy: { matches: attributes-before } }
    - any:
        - not: { follows: { kind: attribute_item, regex: 'derive\([^)]*\bClone\b', stopBy: { matches: attributes-before } } }
        - not: { follows: { kind: attribute_item, regex: 'derive\([^)]*\bPartialEq\b', stopBy: { matches: attributes-before } } }
    - not:  # a cause (#[source], #[from], or a field named source) may be neither Clone nor PartialEq
        has:
          stopBy: end
          any:
            - { kind: attribute_item, regex: '^#\[(source|from)\]$' }
            - { kind: field_declaration, has: { field: name, regex: '^source$' } }
```

The infrastructure list names types as they are written; an error imported as a bare `Error`
is not seen, so write adapter errors with their path.

### Dependencies

Philosophy: "The standard library SHOULD be preferred over new dependencies unless a crate
provides clear value." The value is written down when the crate is added, and two checks hold it:
every dependency (normal, dev and build) has an approval reason, and none is unused.

```toml
# Cargo.toml: one line per dependency, saying what it earns that the standard library does not.
[package.metadata.approved-dependencies]
serde = "the wire format of every boundary type"
thiserror = "typed errors without hand-written Display and Error impls"
proptest = "property tests where a law exists (Testing Strategy)"
```

```bash
# A dependency without an approval reason. Holds Philosophy: std first, each crate added on purpose. Needs jq.
cargo metadata --format-version 1 --no-deps | jq -r '.packages[] | . as $p | .dependencies[] | (.rename // .name) as $d | select((($p.metadata // {})["approved-dependencies"] // {})[$d] // "" | length == 0) | "\($p.name): \($d) (\(.kind // "normal")) has no reason in [package.metadata.approved-dependencies]"' | (! grep .)
# A dependency no code uses. Holds Philosophy: every crate earns its place. cargo install cargo-machete; verified on 0.9.2.
cargo machete
```

`cargo machete` reads source, not the compiled crate, so a crate used only inside a macro's
expansion looks unused. List it under `[package.metadata.cargo-machete] ignored`, with a comment
saying why.

### Rejection coverage

Testing Strategy, Budget: "one rejected input per distinct reason for rejection", and a test for
each forbidden transition. A tool proves every rejection in domain code is reached by a test.
ast-grep lists each `Err(..)` under a `domain` path, and each `None` in a function returning
`Option`. [cargo-llvm-cov](https://github.com/taiki-e/cargo-llvm-cov) runs the tests and records
how often each region of code ran; install it with `cargo install cargo-llvm-cov --locked` and
`rustup component add llvm-tools-preview` (verified on 0.9.1). A jq join then fails on any
rejection that no test reached.

```yaml
# .ast-grep/coverage/domain-rejection.yml, outside ruleDirs: it lists rejections for the join below and judges nothing itself
# A rejection in domain code: an Err(..), or a None where the function returns Option.
# Holds Testing Strategy, Budget, through the join below.
id: domain-rejection
language: rust
severity: hint
message: A rejection in domain code.
files: ["**/domain/**"]
rule:
  any:
    - pattern: Err($$$)
    - all:
        - pattern: None
        - not: { inside: { kind: match_pattern, stopBy: end } }  # a None pattern matches a value; it rejects nothing
        - inside: { kind: function_item, stopBy: end, has: { field: return_type, regex: '^Option\b' } }
```

```bash
# A rejection in domain code that no test reaches. Holds Testing Strategy, Budget. Needs jq; run at the workspace root.
cargo llvm-cov --json --output-path target/coverage.json
ast-grep scan --rule .ast-grep/coverage/domain-rejection.yml --json=compact | jq -r --slurpfile cov target/coverage.json '($cov[0].data[0].files | map({(.filename): .segments}) | add) as $segments | .[] | . as $r | (.range.start.line + 1) as $l | (.range.start.column + 1) as $c | [($segments[$ENV.PWD + "/" + .file] // [])[] | select(.[3] and (.[0] < $l or (.[0] == $l and .[1] <= $c)))] | select(last == null or last[2] == 0) | "\($r.file):\($l): no test reaches this rejection: \($r.text)"' | (! grep .)
```

The join reads the region each rejection starts in, not its line, so
`if n == 0 { None } else { Some(Self(n)) }` on one line is judged on its own. It cannot see a
rejection with no `Err` or `None` of its own (`?`, `ok_or(PortError::Zero)`, a combinator), nor
whether the test that reached a rejection asserted on it. Review keeps both.

### Type-aware lints: dylint, for a long-lived codebase

Some rules need to know what a type is, who implements a trait, or which function a call reaches.
[dylint](https://github.com/trailofbits/dylint) runs custom lints built against the compiler, and the
library `rust_type_driven_lints` (`dev/rust-type-driven/lints` in this skill's repository) holds six.
Its cost is a pinned nightly toolchain, about 1.5 GB fetched on the first run, and a rebuild whenever
that nightly moves: adopt it in a codebase meant to live for years, not in every project.

```toml
# Cargo.toml, at the workspace root: where the lints come from, and the cfg dylint sets while it runs
[workspace.metadata.dylint]
libraries = [{ git = "https://github.com/leodutra/agent-skills", pattern = "dev/rust-type-driven/lints" }]

[lints.rust]
unexpected_cfgs = { level = "warn", check-cfg = ['cfg(dylint_lib, values(any()))'] }
```

```bash
# The type-aware rules below. cargo install cargo-dylint dylint-link; verified on 6.1.0.
# --all-targets compiles the tests too, where single_impl_trait can see the test doubles.
DYLINT_RUSTFLAGS="-D warnings" cargo dylint --all -- --all-targets
```

| Lint | Catches | Holds |
| --- | --- | --- |
| `pub_field_on_invariant_type` | a `pub` field on a type with a fallible constructor (an associated fn without `self` returning `Result<Self, _>` or `Option<Self>`, or a `TryFrom` or `FromStr` impl) | Type-Driven Design: a refinement's fields are private |
| `refinement_escape` | on a type with a fallible constructor: an impl of `Deref`, `DerefMut`, `AsMut` or `BorrowMut`, or a public method returning `&mut` | Newtypes, Invariant integrity: no `&mut` to the inner value, no `Deref` |
| `error_not_std_error` | `()`, or a type of this crate that is not `std::error::Error + Send + Sync`, as a public fn's error or a `FromStr` or `TryFrom` impl's | Error Modeling: an error type implements `std::error::Error + Send + Sync + 'static` |
| `blocking_in_async` | a call into `std::fs`, `std::net`, `std::thread::sleep`, a `std::process` wait or stdin inside an `async fn` or block, outside a closure such as `spawn_blocking`'s | Async, Blocking work: async code never blocks the runtime |
| `primitive_domain_param` | a heuristic: a `pub fn` in a `domain` module taking `String`, `&str`, an integer or `uuid::Uuid` for a parameter named `id`, `*_id`, `email`, `name` or `amount` | Type-Driven Design: a value with an invariant, or one swappable with another of its primitive, gets a newtype |
| `single_impl_trait` | a trait not exported from the crate with exactly one implementation, test doubles included | Dependency Injection: no trait for a single implementation without a second one or a test double |

A finding that is wrong, most likely the heuristic's, is silenced where it is wrong, with a reason:
`#[cfg_attr(dylint_lib = "rust_type_driven_lints", expect(primitive_domain_param, reason = "…"))]`.

---

## Code Review Checklist

The tools above hold these rules, and review never re-checks them: `_ =>` on your own enums;
`unwrap()`, `expect()`, `panic!`, `todo!`, `unimplemented!`, `unreachable!` outside tests; `unsafe`,
and an unsafe block without a `// SAFETY:` comment; a public type without `Debug`; a `PartialEq`
without the `Eq` it could have; a spawned future without `Send`; a lock held across `.await`; an
owned parameter where a borrow would do; a redundant clone; bool flags for exclusive states;
`anyhow` or `eyre` in library code; interior mutability in domain types; ambient time or randomness
in domain code; a refinement that serde or sqlx builds without its constructor, or that derives
`Default`; a newtype without `Clone`, `PartialEq`, `Eq` and `Hash`; a yes-or-no validation; a
`TryFrom` that cannot fail; a `try_new` without an infallible `new`; a `const fn literal` called
outside a `const` item; a stringly typed error; an error message that is capitalized or ends in a
period; a domain error without `Clone` and `PartialEq`; an infrastructure error held without
`#[source]`; generic role names; a dependency without an approval reason; an unused dependency; a
rejection in domain code that no test reaches; formatting.

Review checks only what no tool can decide. Where the dylint library is adopted, it holds the items
marked (dylint), and review looks only at what it cannot see:

- [ ] Any raw `String`, `&str`, integer or `Uuid` naming a domain concept in a domain signature? Take the newtype. (dylint, for the parameter names it knows)
- [ ] Any public field, or variant field, on a type with an invariant? Make it private behind a constructor. (dylint, for struct fields)
- [ ] Any `Deref`, `DerefMut`, or `&mut` to the inner value on a refinement? Offer `as_str()`, `get()`, `AsRef` or `into_inner()`. (dylint)
- [ ] Any error type that is not `std::error::Error + Send + Sync`? Derive `thiserror::Error`. (dylint)
- [ ] Any sentinel, or pair of `Option`s, standing for exclusive states? Use one enum.
- [ ] Any validation after parsing? Remove it.
- [ ] Any `FromStr`, `TryFrom`, serde or database decode that checks on its own instead of delegating to the one validating function? Delegate.
- [ ] Any constructor returning `Option` for more than one reason, or checking before it normalizes (trim, case)? Return a `Result` with an error enum; normalize first.
- [ ] Any mutating method on a refinement that can break its invariant? Make it keep the invariant, or remove it.
- [ ] Any `Display` and `FromStr` pair without a round-trip property test? Add one.
- [ ] Any secret with a derived `Debug`, a `Display` or a `Serialize`, or an error message echoing it? Redact it.
- [ ] Any hand-written `Borrow<str>` whose `Eq`, `Hash` or `Ord` differ from the inner type's? Remove it.
- [ ] Any approval reason in `[package.metadata.approved-dependencies]` that the standard library answers? Remove the crate.
- [ ] Any trait with a single implementor and no test double? Remove it. (dylint)
- [ ] Any `clone()` in a hot path, even a needed one? Restructure or document it.
- [ ] Any infrastructure error crossing a boundary untranslated? Translate it into the caller's error type.
- [ ] Any `assert!()` / `debug_assert!()` guarding what should be a type or typed error? Re-encode it.
- [ ] Any async path vulnerable to cancellation? Make it idempotent or transactional.
- [ ] Any async code blocking the runtime? Use async-aware APIs or `spawn_blocking`. (dylint, for the calls it lists)
- [ ] Any rejection with no `Err` or `None` of its own (`?`, `ok_or`), or a test that reaches a rejection without asserting on its error? Pin the error in the test.
- [ ] Any test beyond the budget (a second example of a rule already pinned, a getter, a derive)? Remove it.

---

## Commands

```bash
cargo check                                  # first: fastest compile feedback
cargo fmt --check
cargo clippy --all-targets -- -D warnings    # --all-targets lints tests too
cargo test
ast-grep scan                                # the syntax rules
cargo machete                                # no unused dependency
cargo metadata --format-version 1 --no-deps | jq -r '…' | (! grep .)   # each dependency approved: the full line is under Dependencies
cargo llvm-cov --json --output-path target/coverage.json                # the tests again, recording what ran
ast-grep scan --rule .ast-grep/coverage/domain-rejection.yml --json=compact | jq … | (! grep .)   # every rejection tested: the full line is under Rejection coverage
DYLINT_RUSTFLAGS="-D warnings" cargo dylint --all -- --all-targets   # where the dylint library is adopted
```

All nine MUST pass before a task is considered complete, locally and in CI, and the tenth where
the dylint library is adopted.

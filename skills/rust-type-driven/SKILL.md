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
  contains `domain`), and records and DTOs elsewhere, so the two are never mistaken for each other.

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

  The field says which, so a reader tells the two apart at the definition.
- Enum variant fields are always public. A variant whose fields share an invariant
  (`sale < regular`) MUST wrap a private-field struct instead of carrying the fields itself.
- Absence MUST be an `Option` with one stated meaning, or a variant. Sentinels (`""`, `0`,
  `-1`) MUST NOT stand for absence. When `None` would mean two things, use an enum.
- Enums + structs SHOULD be preferred over class hierarchies.
- State transitions SHOULD default to immutable values.

### Newtypes

A refinement's rules. Read [references/newtypes.md](references/newtypes.md) when adding or
reviewing one: it holds the error, serde, clap, database and std trait rules, and a complete
template that passes this skill's lints.

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
- Generic role names like `Service`, `Manager`, `Helper`, `Utils`, and `Misc` MUST NOT be introduced.

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
- Every rejection reason in domain code MUST be reached by a test.

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

A rule the compiler or clippy can check MUST be checked by them, not by an agent's or a reviewer's
reading: a lint runs on every change, whoever made it, and cannot be talked out of a verdict. Only
lints that already exist in rustc and clippy are used, so there is nothing to install. Every other
rule is held by review (Code Review Checklist).

To adopt them, paste [assets/lints.toml](assets/lints.toml) into `Cargo.toml`, and copy
[assets/clippy.toml](assets/clippy.toml) to each crate's root. Each lint in those files names what
it catches and the rule it holds. `cargo clippy --all-targets -- -D warnings` (Commands) then
checks them on every change; the Code Review Checklist lists what they hold, so review never
re-checks it.

The test allowances cover `#[cfg(test)]` code only. Each file under `tests/` is its own crate,
so the denies apply there in full: integration tests SHOULD return `Result<(), Box<dyn Error>>`
and use `?`.

A lint that misfires is silenced where it misfires, with `#[expect(clippy::name, reason = "…")]`,
never switched off for the crate.

---

## Code Review Checklist

The lints above hold these rules, and review never re-checks them: `_ =>` on your own enums;
`unwrap()`, `expect()`, `panic!`, `todo!`, `unimplemented!`, `unreachable!` outside tests; `unsafe`,
and an unsafe block without a `// SAFETY:` comment; a public type without `Debug`; a `PartialEq`
without the `Eq` it could have; a `TryFrom` that cannot fail; `()` as a public fn's error; a struct
mixing `pub` and private fields; a spawned future without `Send`; a lock or `RefCell` borrow held
across `.await`; an owned parameter where a borrow would do; a redundant clone; bool flags for
exclusive states; `anyhow` or `eyre` in library code; interior mutability in domain types; ambient
time or randomness in domain code; formatting.

Review checks the rest:

**Types and parsing**

- [ ] Any raw `String`, `&str`, integer or `Uuid` naming a domain concept in a domain signature? Take the newtype.
- [ ] Any public field on a refinement, or variant fields sharing an invariant? Make them private behind a constructor.
- [ ] Any refinement built without its constructor: a plain `derive(Deserialize)`, `serde(transparent)`, `sqlx(transparent)`, or a `Default` that is not valid? Route it through `try_from`, or remove the derive.
- [ ] Any `is_valid_*` or `validate` returning `bool` or `Result<()>`, or validation after parsing? Replace it with a constructor that returns the type.
- [ ] Any `FromStr`, `TryFrom`, serde or database decode that checks on its own instead of delegating to the one validating function? Delegate.
- [ ] Any sole fallible constructor not named `new`, or a `try_new` without an infallible `new`? Rename it.
- [ ] Any constructor returning `Option` for more than one reason, or checking before it normalizes? Return a `Result` with an error enum; normalize first.
- [ ] Any `Deref`, `DerefMut`, `AsMut`, or `&mut` to the inner value on a refinement, or a mutating method that can break its invariant? Offer `as_str()`, `get()`, `AsRef` or `into_inner()`; keep the invariant or drop the method.
- [ ] Any newtype without `Clone`, `PartialEq`, `Eq` and `Hash`, or a hand-written `Borrow<str>` that disagrees with them? Derive them; remove the `Borrow`.
- [ ] Any `const fn literal` called outside a `const` item? Bind it to a `const`.
- [ ] Any sentinel, or pair of `Option`s, standing for exclusive states? Use one enum.

**Errors**

- [ ] Any stringly typed error (`Err("…".into())`, `Result<_, String>`), or an error type that is not `std::error::Error + Send + Sync`? Use a `thiserror` enum.
- [ ] Any domain error without `Clone` and `PartialEq`, though it holds no cause? Derive them.
- [ ] Any error message that is capitalized, ends in a period, or echoes secret input? Rewrite it.
- [ ] Any infrastructure error held without `#[source]`, or crossing a boundary untranslated? Keep the cause; translate it into the caller's error type.
- [ ] Any secret with a derived `Debug`, a `Display` or a `Serialize`? Redact it.

**Tests**

- [ ] Any rejection reason in domain code that no test reaches, or a test that reaches one without asserting on its error? Add the test; pin the error.
- [ ] Any `Display` and `FromStr` pair without a round-trip property test? Add one.
- [ ] Any test beyond the budget (a second example of a rule already pinned, a getter, a derive)? Remove it.

**Design**

- [ ] Any generic role name (`Service`, `Manager`, `Helper`, `Utils`, `Misc`)? Name the capability.
- [ ] Any trait with a single implementor and no test double? Remove it.
- [ ] Any dependency the standard library covers, or one no code uses? Remove it.
- [ ] Any `clone()` in a hot path, even a needed one? Restructure or document it.
- [ ] Any `assert!()` / `debug_assert!()` guarding what should be a type or typed error? Re-encode it.
- [ ] Any async code blocking the runtime? Use async-aware APIs or `spawn_blocking`.
- [ ] Any async path vulnerable to cancellation? Make it idempotent or transactional.

---

## Commands

```bash
cargo check                                  # first: fastest compile feedback
cargo fmt --check
cargo clippy --all-targets -- -D warnings    # --all-targets lints tests too
cargo test
```

All four MUST pass before a task is considered complete, locally and in CI.

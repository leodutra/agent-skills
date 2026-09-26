---
name: rust-type-driven
description: >
  Idiomatic type-driven Rust for domain and backend code: parse-don't-validate at trust
  boundaries, newtypes for domain concepts, illegal states unrepresentable, typed errors
  with thiserror, capability traits, async/cancellation discipline, and invariant testing.
  Use this skill whenever writing, reviewing, refactoring, or designing Rust that models a
  domain — HTTP/RPC handlers, database or queue boundaries, state machines, value objects,
  error types. Trigger on mentions of: parse don't validate, newtype,
  illegal states, typestate, thiserror, anyhow, TryFrom, domain model, validation, Result
  or Option design, trait/DI decisions, tokio tasks, cancellation safety, spawn_blocking,
  proptest. Also trigger when Rust code under review uses raw String/i64/Uuid in signatures,
  stringly typed errors, `_ =>` arms on its own enums, or unwrap()/expect() outside tests.
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

All external data is untrusted. Every trust boundary reparses raw input into validated domain
types: HTTP/RPC, database reads, queues, files, and environment (vars/others).

Rules:

- External data MUST be parsed at the boundary and trusted afterward.
- Inbound conversions SHOULD use `TryFrom` / `TryInto`.
- Outbound conversions SHOULD use `From` / `Into`.
- Code MUST NOT re-check an invariant after successful parsing.
- Domain types MUST NOT derive `Deserialize` structurally: a derived `Deserialize` builds the
  value without calling its constructor, so it skips the parse. Deserialize a record/DTO and
  convert it with `TryFrom`, or route the derive through the constructor with
  `#[serde(try_from = "…")]`.

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
            customer: CustomerId::parse(req.customer_id)?,
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

- Illegal states MUST be unrepresentable.
- A value SHOULD get a newtype when it carries an invariant, or when it could be swapped with
  another value of the same primitive (`StoreName` / `StoreAddress`). A value with neither
  SHOULD NOT be wrapped.
- Fields of a type with an invariant MUST be private; a fallible constructor is the only way in.
- Enum variant fields are always public. A variant whose fields share an invariant
  (`sale < regular`) MUST wrap a private-field struct instead of carrying the fields itself.
- Absence MUST be an `Option` with one stated meaning, or a variant. Sentinels (`""`, `0`,
  `-1`) MUST NOT stand for absence. When `None` would mean two things, use an enum.
- States that exclude each other MUST be one enum, not several `bool` flags or `Option`s.
- Typestate SHOULD be used only when the state is known statically at every call site and
  invalid transitions are costly. State read from storage or the wire MUST be an enum, since
  its value is known only at runtime.
- Enums + structs SHOULD be preferred over class hierarchies.
- State transitions SHOULD default to immutable values.

### Newtypes

```rust
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Email(String);

// No pub constructor. The only way to get an Email is through parse().
// After parse() succeeds, the Email is trusted everywhere — no re-validation.
impl Email {
    pub fn parse(raw: impl Into<String>) -> Result<Self, ValidationError> {
        let value = raw.into();
        if value.contains('@') && value.len() <= 254 {
            Ok(Self(value))
        } else {
            Err(ValidationError::InvalidEmail(value))
        }
    }

    pub fn as_str(&self) -> &str {
        &self.0
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
#[derive(Debug, thiserror::Error)]
pub enum OrderError {
    #[error("cannot transition from {from} to {to}")]
    InvalidTransition { from: OrderStatus, to: OrderStatus },
    #[error("order total exceeds credit limit: {total} > {limit}")]
    CreditLimitExceeded { total: Money, limit: Money },
    #[error("empty order")]
    EmptyOrder,
}

// The adapter translates its infrastructure error at the boundary and keeps it as the cause.
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
- Library code MUST return typed errors.
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
- Constructors SHOULD accept owned-friendly inputs such as `impl Into<String>` and return owned values.
- Important return values SHOULD use `#[must_use]` when ignoring them is likely a bug.
- Time and randomness SHOULD be parameters, not ambient calls (`Utc::now()`, `rand`) inside
  domain logic. That is what keeps domain tests deterministic.
- Generic role names like `Service`, `Manager`, `Helper`, `Utils`, and `Misc` MUST NOT be introduced (checked by the grep under Enforce with Tools).

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
- State transitions SHOULD be tested for each forbidden transition the type cannot rule out.

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
    fn money_cents_roundtrip(cents in 1i64..=i64::MAX) {
        let money = Money::from_cents(cents).unwrap();
        prop_assert_eq!(money.cents(), cents);
    }
}
```

### What not to test

- Private helpers SHOULD be tested through the public API.
- Framework glue SHOULD NOT be tested unless custom logic is involved.
- Tests SHOULD NOT target what the compiler already guarantees, nor derives, getters or `Display`.

---

## Enforce with Tools

A rule a deterministic tool can check (the compiler, clippy, rustfmt, a grep in CI) MUST be checked
by that tool, not by an agent's or a reviewer's reading. Review covers only what no tool can decide.
A tool is repeatable and cannot be talked out of a verdict; a reading is neither.

```toml
# Cargo.toml — each lint names what it catches, then the rule it holds and where that rule lives above.
[lints.rust]
# Any `unsafe` at all. Philosophy: unsafe minimized; a crate that truly needs it lifts this with a stated reason.
unsafe_code = "forbid"

[lints.clippy]
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

Generic role names are a grep, since clippy cannot see type names. It holds Behavior Rules: no
`Service`, `Manager`, `Helper`, `Utils` or `Misc` types.

```bash
! rg -n --type rust '\b(struct|enum|trait|type)\s+\w*(Service|Manager|Helper|Utils|Misc)\b' src/
```

---

## Code Review Checklist

The tools above hold these rules, and review never re-checks them: `_ =>` on your own enums;
`unwrap()`, `expect()`, `panic!`, `todo!`, `unimplemented!`, `unreachable!` outside tests;
`unsafe`; a spawned future without `Send`; a lock held across `.await`; an owned parameter where
a borrow would do; a redundant clone; bool flags for exclusive states; `anyhow` or `eyre` in
library code; interior mutability in domain types; ambient time or randomness in domain code;
generic role names; formatting.

Review checks only what no tool can decide:

- [ ] Any raw `String`, `i64`, or `Uuid` naming a domain concept in a signature? Wrap in a newtype.
- [ ] Any domain type deriving `Deserialize` structurally? Parse through a record or `#[serde(try_from)]`.
- [ ] Any public field, or variant field, on a type with an invariant? Make it private behind a constructor.
- [ ] Any sentinel, or pair of `Option`s, standing for exclusive states? Use one enum.
- [ ] Any validation after parsing? Remove it.
- [ ] Any `Err("…".into())` or other stringly typed error? Use a typed variant.
- [ ] Any new dependency where the standard library would be enough? Remove or justify it.
- [ ] Any trait with a single implementor and no test double? Remove it.
- [ ] Any `clone()` in a hot path, even a needed one? Restructure or document it.
- [ ] Any infrastructure error crossing a boundary raw, or a cause dropped? Translate it, keep `#[source]`.
- [ ] Any `assert!()` / `debug_assert!()` guarding what should be a type or typed error? Re-encode it.
- [ ] Any async path vulnerable to cancellation? Make it idempotent or transactional.
- [ ] Any async code blocking the runtime? Use async-aware APIs or `spawn_blocking`.
- [ ] Each constructor tested once accepted and once per rejection reason? Add what is missing, and nothing beyond it.

---

## Commands

```bash
cargo check                                  # first: fastest compile feedback
cargo fmt --check
cargo clippy --all-targets -- -D warnings    # --all-targets lints tests too
cargo test
! rg -n --type rust '\b(struct|enum|trait|type)\s+\w*(Service|Manager|Helper|Utils|Misc)\b' src/
```

All five MUST pass before a task is considered complete, locally and in CI.

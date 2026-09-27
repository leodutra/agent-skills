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
  `#[serde(try_from = "…")]`. A fieldless enum MAY derive it: every value it can hold is valid.
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
- A fallible constructor MUST be named `parse` (from raw input) or `try_new`, never `new`: `new`
  reads as infallible, and mutation testing (Enforce with Tools) skips any function named `new`,
  so its rejection tests would go unchecked.
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
    pub fn try_new(sale: Money, regular: Money) -> Result<Self, PriceError> {
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

### Syntax rules: ast-grep

What clippy cannot see, a syntax pattern can: attributes on a type, the shape of an error value, a
type's name. [ast-grep](https://ast-grep.github.io) (`cargo install ast-grep --locked`; these rules
were verified on 0.45.3) matches the syntax tree, so a comment or a string that mentions a name
never counts. `ast-grep scan` exits non-zero on any finding.

```yaml
# sgconfig.yml, at the repository root
ruleDirs:
  - .ast-grep/rules
```

```yaml
# .ast-grep/rules/domain-structural-deserialize.yml
# A domain type deriving Deserialize, which builds it without its constructor.
# Holds Parse, Don't Validate: "Domain types MUST NOT derive Deserialize structurally".
id: domain-structural-deserialize
language: rust
severity: error
message: A domain type derives Deserialize without its constructor.
note: "Parse, Don't Validate: deserialize a record and convert it with TryFrom, or add #[serde(try_from = \"...\")]."
files: ["**/domain/**"]  # the domain path convention above; records and DTOs live elsewhere
utils:
  attributes-before:  # the attributes and comments directly above an item
    not: { any: [{ kind: attribute_item }, { kind: line_comment }, { kind: block_comment }] }
rule:
  all:
    - any: [{ kind: struct_item }, { kind: enum_item }]
    - follows: { kind: attribute_item, regex: 'derive\([^)]*\bDeserialize\b', stopBy: { matches: attributes-before } }
    - not:
        follows: { kind: attribute_item, regex: 'serde\([^)]*\btry_from\b', stopBy: { matches: attributes-before } }
    - not:  # a fieldless enum has no invalid value, so a derive skips no parse
        all:
          - kind: enum_item
          - not: { has: { stopBy: end, any: [{ kind: ordered_field_declaration_list }, { kind: field_declaration_list }] } }
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
# .ast-grep/rules/fallible-new.yml
# A constructor named `new` that can fail.
# Holds Type-Driven Design: "A fallible constructor MUST be named parse or try_new, never new" (mutation testing skips `new`).
id: fallible-new
language: rust
severity: error
message: A fallible constructor is named `new`.
note: "Type-Driven Design: name it parse (from raw input) or try_new; cargo-mutants never mutates a function named new."
rule:
  kind: function_item
  all:
    - has: { field: name, regex: '^new$' }
    - has: { field: return_type, regex: '^(\w+::)*Result\b' }  # Result or io::Result; an Option-returning new stays legal
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

### Mutation testing

Testing Strategy, Budget: "one accepted input and one rejected input, plus one rejected input per
distinct reason for rejection". A tool proves it: [cargo-mutants](https://mutants.rs)
(`cargo install cargo-mutants`; verified on 27.1.0) breaks each guard of a constructor in turn and
runs the tests. A broken guard that no test notices is a rejection reason nobody tests.

```toml
# .cargo/mutants.toml
# Mutate domain constructors only, so a surviving mutant is exactly a missing rejection test; mutating
# getters would demand the tests Testing Strategy rules out. cargo-mutants skips any fn named `new`,
# which is why a fallible constructor is named parse or try_new.
examine_globs = ["src/domain/**/*.rs"]
examine_re = ["::(parse|try_new|try_from)\\b"]
```

```bash
# A constructor's rejection reason that no test covers. Holds Testing Strategy, Budget. Exits 2 on a missed mutant.
cargo mutants
```

It builds and tests once per mutant, so it runs in CI and before a release, not on every save.
It mutates operators (`>`, `==`, `!`, `&&`) and whole function bodies, not method calls: a guard
that is one call, such as `if raw.is_empty()`, yields no mutant, so review still checks that its
rejection has a test.

---

## Code Review Checklist

The tools above hold these rules, and review never re-checks them: `_ =>` on your own enums;
`unwrap()`, `expect()`, `panic!`, `todo!`, `unimplemented!`, `unreachable!` outside tests;
`unsafe`; a spawned future without `Send`; a lock held across `.await`; an owned parameter where
a borrow would do; a redundant clone; bool flags for exclusive states; `anyhow` or `eyre` in
library code; interior mutability in domain types; ambient time or randomness in domain code;
a domain type deriving `Deserialize` structurally; a stringly typed error; an infrastructure
error held without `#[source]`; a fallible constructor named `new`; generic role names; a
dependency without an approval reason; an unused dependency; a constructor's rejection reason with
no test; formatting.

Review checks only what no tool can decide:

- [ ] Any raw `String`, `i64`, or `Uuid` naming a domain concept in a signature? Wrap in a newtype.
- [ ] Any public field, or variant field, on a type with an invariant? Make it private behind a constructor.
- [ ] Any sentinel, or pair of `Option`s, standing for exclusive states? Use one enum.
- [ ] Any validation after parsing? Remove it.
- [ ] Any approval reason in `[package.metadata.approved-dependencies]` that the standard library answers? Remove the crate.
- [ ] Any trait with a single implementor and no test double? Remove it.
- [ ] Any `clone()` in a hot path, even a needed one? Restructure or document it.
- [ ] Any infrastructure error crossing a boundary untranslated? Translate it into the caller's error type.
- [ ] Any `assert!()` / `debug_assert!()` guarding what should be a type or typed error? Re-encode it.
- [ ] Any async path vulnerable to cancellation? Make it idempotent or transactional.
- [ ] Any async code blocking the runtime? Use async-aware APIs or `spawn_blocking`.
- [ ] Any rejection guard that is a single method call (`is_empty()`), which mutation testing cannot break? Check it has a test.
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
cargo mutants                                # CI and before a release: every rejection reason tested
cargo metadata --format-version 1 --no-deps | jq -r '…' | (! grep .)   # each dependency approved: the full line is under Dependencies
```

All eight MUST pass before a task is considered complete, locally and in CI.

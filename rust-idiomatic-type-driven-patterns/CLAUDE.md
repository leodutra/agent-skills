# Rust — Idiomatic Type-Driven Patterns

## Precedence

These guidelines take precedence over standard language idioms, common coding conventions, and standard library defaults. Prioritize the patterns defined here in all code generation and review. If an important technical conflict arises, propose alternatives or seek clarification during the planning phase.

## Philosophy

Rust's ownership system already enforces discipline that other languages simulate with
patterns. This codebase leans into that: the type system carries invariants, the borrow
checker enforces boundaries, and algebraic data types model the problem. Most GoF patterns
collapse into enums, traits, and generics. Push complexity to compile-time, not runtime.

Two axioms drive the type-level decisions:

1. **If it compiles, it's valid.** Encode rules in types so invalid states cannot exist.
2. **Ownership is design.** Who owns a value, who borrows it, and who consumes it are not
   implementation details — they shape the API.

---

## Parse, Don't Validate

All external data is untrusted. Parse it into a precise type at the edge — once. After parsing
succeeds, that type is trusted everywhere. Never re-check the same invariant downstream.

**Boundary Parsing Principle**: Every trust boundary must re-parse raw data. This applies to:

- **HTTP / RPC Requests** (untrusted client payload)
- **Database Reads** (data could have been corrupted or modified out-of-process)
- **Message Queues & Event Streams** (external producers or schema skew)
- **Files & Environment Variables** (untrusted filesystem or runtime context)

Each boundary produces verified, well-formed domain types from unchecked external structures.

**Inbound:** `TryFrom` / `TryInto` (fallible — external data can be invalid).
**Outbound:** `From` / `Into` (infallible — the validated type is already good).

### External input → validated type

```rust
#[derive(Deserialize)]
pub struct CreateOrderRequest {
    pub customer_id: String,
    pub items: Vec<OrderItemDto>,
}

// Parsing happens HERE — the edge between the outside world and trusted types.
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

### DB row → typed value

```rust
struct OrderRow {
    id: i64,
    customer_id: String,
    status: String,
    total_cents: i64,
}

impl TryFrom<OrderRow> for Order {
    type Error = DataCorruptionError;

    fn try_from(row: OrderRow) -> Result<Self, Self::Error> {
        Ok(Order {
            id: OrderId::new(row.id),
            customer: CustomerId::parse(row.customer_id)
                .map_err(|e| DataCorruptionError::InvalidField("customer_id", e))?,
            status: OrderStatus::parse(&row.status)?,
            total: Money::from_cents(row.total_cents),
        })
    }
}
```

### Env vars → typed config

```rust
pub struct AppConfig {
    pub db_url: DatabaseUrl,        // newtype — validated on construction
    pub pool_size: PoolSize,
    pub port: Port,
}

impl AppConfig {
    pub fn from_env() -> Result<Self, ConfigError> {
        Ok(Self {
            db_url: DatabaseUrl::parse(env_required("DATABASE_URL")?)?,
            pool_size: PoolSize::parse(env_or("DB_POOL_SIZE", "10"))?,
            port: Port::parse(env_or("PORT", "8080"))?,
        })
    }
}
```

---

## Type-Driven Design

### Core rules

- **Parse, don't validate.** Parse once at edges, trust types forever after.
- **Make illegal states unrepresentable.** Use enums with variant-specific data, not structs with optional fields.
- **Newtypes over primitives.** Use newtypes (e.g., `OrderId`, `CustomerId`, `Email`) in meaningful signatures to prevent argument confusion, protect domain invariants, and express business language. Do not over-wrap low-impact, local strings (like `FirstName` or `CityName`) unless they have distinct, structural invariants to maintain.
- **Typestate for workflows.** Model state machines as generic type parameters. Invalid transitions must not compile.
- **ADTs are the modeling language.** Enums + structs replace class hierarchies.
- **Immutable values over mutable state.** State transitions return new values.

### Newtype pattern

```rust
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Email(String);

impl Email {
    pub fn parse(raw: impl Into<String>) -> Result<Self, ValidationError> {
        let s = raw.into();
        if s.contains('@') && s.len() <= 254 {
            Ok(Self(s))
        } else {
            Err(ValidationError::InvalidEmail(s))
        }
    }

    pub fn as_str(&self) -> &str { &self.0 }
}

// No pub constructor. The only way to get an Email is through parse().
// After parse() succeeds, the Email is trusted everywhere — no re-validation.
```

### Making illegal states unrepresentable

```rust
// BAD — optional fields invite invalid combinations
struct Shipment {
    tracking_number: Option<String>,
    delivered_at: Option<DateTime>,
    status: String,  // "pending"? "shipped"? anything?
}

// GOOD — each state carries exactly its valid data
enum Shipment {
    Pending { order_id: OrderId },
    Shipped { order_id: OrderId, tracking: TrackingNumber },
    Delivered { order_id: OrderId, tracking: TrackingNumber, delivered_at: DateTime },
    Cancelled { order_id: OrderId, reason: CancellationReason },
}
```

### When typestate is worth it and when it isn't

**Use typestate** when: the state machine has 3+ states, invalid transitions cause real bugs,
and the type is constructed and consumed across module boundaries.

**Use a plain enum** when: the states are data-only (no behavior differs by state), or the
type is local to a single function.

**Use a smart constructor** (newtype + `parse`) when: there's no state machine, just an
invariant to enforce (e.g., non-empty string, positive integer, valid email).

### Partial updates without invalid states

When only some fields change, model the update as a struct of `Option`s where each *present*
field is already a parsed type. The update can't smuggle in an invalid value, and the type
itself decides whether the transition is legal — the validation stays in one place.

```rust
pub struct OrderUpdate {
    pub new_status: Option<OrderStatus>,    // already a valid enum variant
    pub shipping: Option<ShippingAddress>,  // already a parsed newtype
}

impl Order {
    pub fn apply(self, update: OrderUpdate) -> Result<Self, OrderError> {
        let status = match update.new_status {
            Some(next) => self.status.transition_to(next)?,  // transition rule lives here
            None => self.status,
        };
        Ok(Self { status, ..self })
    }
}

### Healthy Defaults

Only implement the standard `Default` trait when a single, obvious, semantically valid default state exists (e.g., `Vec::new()`, `HashMap::new()`, or configuration structs with secure, robust fallback values).

**Avoid artificial defaults:** Do not implement `Default` for core domain types like `Email`, `Money`, or `Customer` if doing so forces the creation of dummy or nonsensical states (such as placing empty strings/zero/invalid IDs into trusted models). Let compilation fail when a field is missing, or require explicit construction parameters, rather than silencing compilation with a dummy value.

---

## Error Modeling

Errors are typed and structured — never stringly typed.

```rust
#[derive(Debug, thiserror::Error)]
pub enum OrderError {
    #[error("cannot transition from {from} to {to}")]
    InvalidTransition { from: OrderStatus, to: OrderStatus },
    #[error("order total exceeds credit limit: {total} > {limit}")]
    CreditLimitExceeded { total: Money, limit: Money },
    #[error("empty order — at least one item required")]
    EmptyOrder,
}

// Compose lower-level errors into higher-level ones via `From` so `?` just works.
#[derive(Debug, thiserror::Error)]
pub enum AppError {
    #[error(transparent)]
    Order(#[from] OrderError),
    #[error(transparent)]
    Validation(#[from] ValidationError),
    #[error("database query failed")]
    Database(#[from] sqlx::Error),
}
```

### Rules

- Error variants carry **structured context** (types, IDs, amounts) — not format strings.
- `?` composes errors through `From` impls. Write the `From` chain explicitly.
- `thiserror` for typed library errors; `anyhow` / `eyre` only at the top level (`main.rs`, CLI),
  never in reusable library code.
- No `Err("something went wrong".into())`.

---

## Invariants and Assertions

The type system is the first and best place to enforce an invariant — but not every invariant
can be encoded in a type. When one can't, be deliberate about *how* it fails. There's an
escalation order:

1. **Encode it in a type.** A non-empty list → `NonEmpty<T>`. A parsed value → a newtype.
   *If the invariant can be represented in the type system, do not enforce it with a runtime assertion.*
2. **Return a typed error** for anything recoverable — bad input, a failed transition, a violated
   rule. These are expected at runtime, not bugs.
3. **Assert only for "impossible" states** — conditions that, if false, mean the program has a bug,
   not that the input was bad.

```rust
impl Order {
    pub fn confirm(self) -> Result<ConfirmedOrder, OrderError> {
        // Recoverable: a caller can legitimately hit this → typed error.
        if self.total > self.credit_limit {
            return Err(OrderError::CreditLimitExceeded {
                total: self.total,
                limit: self.credit_limit,
            });
        }

        // "Impossible" by construction: Order can only be built with >=1 item.
        // If this ever fires, a constructor invariant was broken — that's our bug, not bad input.
        debug_assert!(!self.items.is_empty(), "Order invariant violated: empty items");

        Ok(ConfirmedOrder { /* ... */ })
    }
}
```

Rules:

- Encode invariants in types first; assertions are the fallback, not the default.
- Return typed errors for recoverable runtime failures (bad input, invalid transition, rule violation).
- Use `debug_assert!()` for impossible states that indicate a programmer mistake — it costs nothing in release builds.
- Use `assert!()` (always on) only when continuing past the violation would be unsafe or corrupt state.
- Never use assertions for user input validation — that's `parse`, returning a typed error.
- Prefer exhaustive `match` over `unreachable!()`; reach for `unreachable!()` only when the
  compiler can't see the exhaustiveness and a typed error makes no sense.

> If an invariant can be represented in the type system, do not enforce it with a runtime assertion.

---

## Behavior Rules

- **Tell, don't ask.** Don't inspect state then decide externally — give types the info they need and let them act.
- **Railway-oriented.** Chain operations through `Result` / `Option` pipelines with `and_then`, `map`, `map_err`.
- **Total functions.** Handle all input cases. No panics on valid input.
- **Exhaustive matching.** No `_` catch-alls unless justified (e.g., `#[non_exhaustive]` from external crates).

### Function design

- Small: one level of abstraction per function.
- Single-purpose: one reason to change.
- Return values over performing side effects.
- Closures for behavior injection by default; traits only when closures are insufficient
  (object safety needed, or the behavior has multiple methods).

### Mutation discipline

- Default to immutable style APIs. Value transformations return new instances.
- Expose `&mut self` when local in-place mutation is the natural conceptual model (e.g., updating a buffer, modifying cache contents), improves performance significantly, or avoids roundtrip object allocations.
- Require justification or explicit design when exposing public `&mut self` methods across core module boundaries.
- Interior mutability (`Cell`, `RefCell`, `Mutex`) is a code smell in pure, side-effect-free domain logic — justify every use with multithreading or structural dependency needs.
- Prefer ownership-first APIs over incidental cloning, but freely clone in cold/configuration/administrative paths when it simplifies ownership.

### Allocation & Zero-Copy Discipline

- **Owned Types (`String`, `Vec<T>`)** are the default for long-lived application state, domain models stored in memory, database rows, and cross-thread messaging.
- **Borrowed Types (`&str`, `&[T]`)** are for quick validation, short-lived helper variables, and zero-allocation parsing at the very edge of input processing.
- **`Cow<'a, T>` (Clone-on-Write)** is for data that is mostly read-only but occasionally requires cloning/mutating (e.g., unescaping strings or templating).
- **Rule of thumb:** Do not introduce reference lifetimes into structs unless you have profiled the application and verified that allocation is a performance bottleneck. Owned APIs are vastly easier to compose, refactor, and spawn across tasks.

---

## Dependency Injection

- Traits define **capabilities** — name them by what they do, not by a structural role: `trait LoadOrders`, `trait ChargePayment`.
- Callers receive these as generic parameters or trait objects; test doubles implement the same traits.

### When to introduce a trait

| Situation                                          | Use a trait? |
|----------------------------------------------------|--------------|
| 2+ real implementations (Postgres + SQLite)        | Yes          |
| 1 real impl but need test doubles for side effects | Yes          |
| Pure function with no side effects                 | No — just call it |
| Single impl, easily testable directly              | No — premature abstraction |

Closures are often enough for simple injection:

```rust
fn process_order(
    order: Order,
    calculate_tax: impl Fn(&Order) -> Money,   // injected behavior, no trait needed
) -> OrderSummary {
    let tax = calculate_tax(&order);
    OrderSummary::new(order, tax)
}
```

---

## Naming

- Types represent **meaning**, not structure: `Email` not `ValidatedString`.
- Functions describe **what**, not **how**: `register_user` not `insert_user_into_db`.
- Constructors: `new`, `parse`, `with_capacity`, `from_*`.
- Conversions: `to_*` (allocates), `as_*` (borrowed view), `into_*` (consuming).
- Booleans: `is_` or `has_` prefix.
- Ban: `data`, `info`, `item`, `handler`, `manager`, `service`, `utils`, `helpers`, `misc`.
- Use vocabulary from the problem you're solving — not programmer jargon.

---

## Pattern Palette

**Use freely:** newtypes, ADTs (enum modeling), `TryFrom`/`From` at edges, `Result`/`Option` pipelines, tell-don't-ask, function composition, module facades, traits-as-capabilities, smart constructors, exhaustive matching.

**Use when justified:** typestate (3+ states, cross-module), builder (many optional params), trait-based strategy (when closures won't do — multiple methods needed), `Arc<dyn Trait>` (genuinely heterogeneous collections).

**Avoid:** Visitor (use `match`), Singleton (use DI), classic Factory (use `TryFrom`/`parse`), `Box<dyn Any>` downcasting, marker traits without compiler enforcement.

---

## Anti-Patterns to Reject

- `UserService` / `OrderManager` god objects accumulating unrelated logic.
- Raw `String`, `i64`, `Uuid` leaking through meaningful function signatures.
- `Err("something went wrong".into())` — string errors.
- `_ => {}` silencing the compiler on your own enums.
- Re-validating the same invariant in multiple places after it's been parsed once.
- Traits with a single implementor and no test double.
- Public `&mut self` methods exposed blindly in core transactional APIs where pure functional transformations describe the domain better.
- `clone()` in hot paths or large-object loops without a reason — redesign ownership or document why clone is acceptable.
- God-mode `App` or `Context` struct passed everywhere.

---

## Async / Runtime Rules

### Boundary constraints (`Send` / `Sync` / `'static`)

- Values crossing task boundaries (`tokio::spawn`, work queues, background workers) must satisfy runtime constraints explicitly (`Send + 'static` when required).
- Avoid borrowing non-`'static` references into spawned tasks; move owned data instead.
- Prefer `Arc<T>` + immutable state over shared mutable state; if mutation is necessary, justify the synchronization primitive.
- Treat `spawn_blocking` as a boundary for CPU/blocking IO work only.

### Cancellation safety

- Treat every `await` as a cancellation point.
- For workflows touching money, inventory, irreversible external effects, or user-visible state,
  use transaction boundaries and idempotent operations so cancellation never leaves a partial,
  externally visible side effect.

### Panic policy

- `panic!` / `unwrap()` / `expect()` are forbidden in production paths.
- Allowed in tests and in irrecoverable bootstrap failures in `main.rs` (with a clear crash message).
- Library code returns typed errors, not panics, for invalid runtime input or dependency failure.
- At any panic boundary (FFI, task supervisor), convert the panic to a controlled failure signal.

---

## Before / After: Common Refactorings

### Primitive obsession → newtypes

```rust
// BEFORE — can silently swap customer_id and order_id
fn cancel_order(customer_id: i64, order_id: i64) -> Result<()> { ... }

// AFTER — compiler rejects swapped arguments
fn cancel_order(customer: CustomerId, order: OrderId) -> Result<(), OrderError> { ... }
```

### Scattered validation → parse-once edge

```rust
// BEFORE — validates in handler, again in repo, again in model
fn handler(email: String) {
    if !email.contains('@') { panic!("bad email"); }   // handler validates
    save_user(email.clone());                           // repo validates again?
}

// AFTER — parsed once, trusted everywhere
fn handler(req: RegisterRequest) -> Result<(), AppError> {
    let cmd = RegisterInput::try_from(req)?;  // Email::parse() happens here
    save_user(cmd.email);                     // Email type is trusted — no check
    Ok(())
}
```

---

## Tradeoff Rules

Guidance that doesn't say "when not to" is dogma. Apply judgment.

| If you're tempted to...                 | Ask first                                                              |
|-----------------------------------------|------------------------------------------------------------------------|
| Add typestate to a 2-state enum         | Is a simple enum with a `transition()` method enough?                  |
| Create a trait for one implementation   | Will there ever be a second impl, or do you just need a test double?   |
| Wrap every primitive in a newtype       | Does this primitive cross a module boundary? If it's local, don't wrap.|
| Make everything immutable               | Is this a hot loop mutating a buffer? Local `mut` is fine.             |
| Split a file into 5 modules             | Is the file >300 lines? If not, one file is clearer.                   |
| Add `From` impls for every conversion   | Is this conversion used more than once? If not, inline it.             |
| Reach for `Result` chains everywhere    | Is this a straight-line function that can't fail? Just return the value.|
| Ban `clone()` absolutely                | Is this a cold path with small data? A clone is fine. Comment why.     |
| Force immutable-return modeling in hot loops | Would local mutation or data-oriented layout improve cache locality and throughput? |

The goal is **working software with clear boundaries** — not purity for its own sake.

---

## Testing Strategy

### Pure logic (unit tests — fast, no mocks)

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

    #[test]
    fn delivered_order_cannot_be_cancelled() {
        let order = Order::delivered(customer_id(), items(), now());
        let err = order.cancel().unwrap_err();
        assert!(matches!(err, OrderError::InvalidTransition { .. }));
    }
}
```

### Parsing (TryFrom tests — valid and invalid inputs)

```rust
#[test]
fn valid_email_parses() {
    assert!(Email::parse("user@example.com").is_ok());
}

#[test]
fn email_without_at_rejects() {
    assert!(matches!(
        Email::parse("not-an-email"),
        Err(ValidationError::InvalidEmail(_))
    ));
}

#[test]
fn db_row_with_corrupt_status_rejects() {
    let row = OrderRow { status: "yolo".into(), ..valid_row() };
    assert!(matches!(
        Order::try_from(row),
        Err(DataCorruptionError::InvalidField(..))
    ));
}
```

### Property tests (for newtypes and parsers)

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn money_from_cents_roundtrips(cents in 0i64..=i64::MAX) {
        let money = Money::from_cents(cents);
        prop_assert_eq!(money.to_cents(), cents);
    }

    #[test]
    fn parsed_email_always_contains_at(s in ".+@.+") {
        if let Ok(email) = Email::parse(s) {
            prop_assert!(email.as_str().contains('@'));
        }
    }
}
```

### Cancellation safety (async)

For any async workflow that must stay consistent under interruption, add a test that cancels
between awaited steps and asserts no partial, externally visible side effect survives — and that
a retry doesn't double-apply.

```rust
#[tokio::test]
async fn transfer_is_cancellation_safe_between_debit_and_credit() {
    let bank = FakeBank::new();
    let task = tokio::spawn(run_transfer(bank.clone(), valid_transfer()));
    bank.wait_until_debited().await;   // park at a cancellation-sensitive point
    task.abort();
    let _ = task.await;                // JoinError expected

    assert!(bank.is_consistent());     // both legs, or neither
    assert!(bank.no_duplicates());     // retry must not double-apply
}
```

### Test naming

`<unit>_<scenario>_<expected>`: `pending_order_can_transition_to_confirmed`, `email_without_at_rejects`.

### What not to test

- Private helper functions — test through the public API.
- Framework glue (route registration, serde derives) — unless custom logic is involved.
- Things the compiler already guarantees (typestate transitions that don't compile).

### Type invariant checklist

For each meaningful type, document and test:

- Constructor invariants (what `new` / `parse` guarantees forever after).
- Transition invariants (which state changes are valid/invalid).
- Roundtrip invariants (serialize/deserialize and DB roundtrip cannot create invalid values).
- Time / concurrency invariants (ordering, staleness, version-conflict behavior) where relevant.

---

## Code Review Checklist

Before approving any change:

- [ ] Any raw `String`, `i64`, or `Uuid` in meaningful function signatures? → Wrap in newtype.
- [ ] Any validation after parsing (re-checking a parsed type)? → Remove.
- [ ] Any `_ => {}` on your own enum? → Match exhaustively.
- [ ] Any trait with a single implementor and no test double? → Remove the trait.
- [ ] Any `clone()` without a justifying comment in a hot path? → Restructure or comment.
- [ ] Any `unwrap()` / `expect()` outside tests/bootstrap? → Use `?` or handle.
- [ ] Any `anyhow` / `eyre` in reusable library code? → Use a typed error.
- [ ] Any `&mut self` that could be `&self` with a returned new value? → Prefer immutable.
- [ ] Any stringly-typed error (`Err("...".into())`)? → Use a proper variant.
- [ ] Any `assert!()` / `debug_assert!()` guarding something that should be a type or a typed error? → Re-encode it.
- [ ] Any async path vulnerable to cancellation at `await` points? → Ensure idempotent / transactional behavior.
- [ ] Tests cover happy path, at least one error path, and parsing? → Add missing.

---

## Decision Records (ADRs)

Significant or non-obvious decisions get a short ADR: the decision, the context that forced it,
the alternatives rejected, and why. One file per decision, numbered, append-only — supersede an
old ADR with a new one rather than editing it.

The point is durable context. Months later, you (or an LLM working in the repo) can recover *why*
a trade-off or boundary exists instead of re-litigating it from scratch. Keep them short, and skip
the ADR entirely when the decision is obvious from the code.

---

## Commands

```bash
cargo build                         # compile
cargo test                          # run all tests
cargo clippy -- -D warnings         # lint — treat warnings as errors
cargo fmt --check                   # format check
```

Run `cargo clippy` and `cargo test` before considering any task complete.

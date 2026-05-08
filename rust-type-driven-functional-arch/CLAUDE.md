# Rust Project — Type-Driven Functional Architecture

## Philosophy

Rust's ownership system already enforces discipline that other languages simulate with
patterns. This codebase leans into that: the type system carries invariants, the borrow
checker enforces boundaries, and algebraic data types model the domain. Most GoF patterns
collapse into enums, traits, and generics. Complexity lives at compile-time, not runtime.

Three axioms drive every decision:

1. **If it compiles, it's valid.** Encode business rules in types so invalid states cannot exist.
2. **Pure core, thin shell.** Domain logic computes. Infrastructure executes. They never mix.
3. **Ownership is architecture.** Who owns a value, who borrows it, and who consumes it — these
   are not implementation details, they *are* the design.

---

## Architecture: Functional Core / Imperative Shell

```
          ┌─────────────────────────────┐
          │       Interface Layer       │  HTTP handlers, CLI, gRPC
          │  (parse input → commands)   │
          └────────────┬────────────────┘
                       │ commands / queries
          ┌────────────▼────────────────┐
          │     Application Layer       │  Orchestration, use cases
          │  (wire domain + infra)      │  async lives here
          └────────────┬────────────────┘
                       │ pure calls
          ┌────────────▼────────────────┐
          │       Domain Layer          │  Pure types + logic
          │  (no IO, no async, no deps) │  the core
          └────────────┬────────────────┘
                       │ port traits
          ┌────────────▼────────────────┐
          │   Infrastructure Layer      │  DB, HTTP clients, queues
          │  (implements port traits)   │  side effects here
          └─────────────────────────────┘
```

- Domain logic is **pure**: no IO, no async, no database calls, no side effects.
- All effectful operations (DB, HTTP, filesystem, queues) live in infrastructure.
- The application layer orchestrates — it calls domain logic and infrastructure ports.
- Dependencies flow **inward only** — domain never imports from infrastructure or application.

---

## Crate Layout

```
src/
├── main.rs                     # Wiring: build deps, start server/runtime
├── lib.rs                      # Re-exports public API
│
├── domain/                     # Pure core — zero external deps beyond std + domain crates
│   ├── mod.rs                  # Public facade: re-exports only what other layers need
│   ├── model.rs                # Core types: newtypes, enums, value objects
│   ├── error.rs                # Domain error enum
│   ├── logic.rs                # Pure functions operating on domain types
│   └── ports.rs                # Trait definitions (Repository, Notifier, etc.)
│
├── application/                # Use-case orchestration — async allowed here
│   ├── mod.rs
│   ├── commands.rs             # Command structs (input DTOs for writes)
│   ├── queries.rs              # Query structs (input DTOs for reads)
│   └── handlers.rs             # Use-case functions: wire domain + infra
│
├── infrastructure/             # Side effects — implements port traits
│   ├── mod.rs
│   ├── persistence/            # DB adapters (sqlx, diesel, etc.)
│   │   ├── mod.rs
│   │   └── order_repo.rs       # impl OrderRepository for PgOrderRepo
│   ├── http_client/            # External API clients
│   └── config.rs               # Typed config from env/files
│
└── interface/                  # Inbound adapters
    ├── mod.rs
    ├── http/                   # Axum/Actix handlers
    │   ├── mod.rs
    │   ├── routes.rs
    │   └── dto.rs              # Request/response types — parse into domain at boundary
    └── cli/                    # CLI entrypoints if applicable
```

**Rules:**
- `domain/` has **no** dependencies on `application/`, `infrastructure/`, or `interface/`.
- `domain/` Cargo deps: only `thiserror`, `serde` (derive only), and domain math/utility crates.
- `application/` depends on `domain/` only. It receives infra as trait objects or generics.
- `infrastructure/` depends on `domain/` (to implement port traits). Never on `application/`.
- `interface/` depends on `application/` and `domain/` (for types). Calls handlers.
- `main.rs` is the only place all layers meet — it constructs and wires everything.

For a feature that grows beyond 3–4 files, give it its own sub-module inside `domain/`:

```
domain/
├── order/
│   ├── mod.rs          # public facade
│   ├── model.rs        # Order, OrderLine, OrderStatus
│   ├── error.rs        # OrderError
│   ├── logic.rs        # calculate_total, apply_discount — pure fns
│   └── ports.rs        # trait OrderRepository
└── mod.rs              # re-exports domain::order::*
```

---

## Boundary Parsing

All external data is untrusted. Parse it into domain types at the boundary — once. After
parsing succeeds, the domain type is trusted everywhere. Never validate again.

**Inbound:** `TryFrom` / `TryInto` (fallible — external data can be invalid).
**Outbound:** `From` / `Into` (infallible — the domain type is already valid).

### HTTP request → domain type

```rust
// interface/http/dto.rs
#[derive(Deserialize)]
pub struct CreateOrderRequest {
    pub customer_id: String,
    pub items: Vec<OrderItemDto>,
}

// Parsing happens HERE — boundary between outside world and domain
impl TryFrom<CreateOrderRequest> for CreateOrderCommand {
    type Error = ValidationError;

    fn try_from(req: CreateOrderRequest) -> Result<Self, Self::Error> {
        Ok(CreateOrderCommand {
            customer: CustomerId::parse(req.customer_id)?,
            items: req.items
                .into_iter()
                .map(OrderItem::try_from)
                .collect::<Result<Vec<_>, _>>()?,
        })
    }
}
```

### DB row → domain type

```rust
// infrastructure/persistence/order_repo.rs
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
// infrastructure/config.rs
pub struct AppConfig {
    pub db: DatabaseConfig,
    pub server: ServerConfig,
}

pub struct DatabaseConfig {
    pub url: DatabaseUrl,        // newtype — validated on construction
    pub max_connections: PoolSize,
}

impl AppConfig {
    pub fn from_env() -> Result<Self, ConfigError> {
        Ok(Self {
            db: DatabaseConfig {
                url: DatabaseUrl::parse(env_required("DATABASE_URL")?)?,
                max_connections: PoolSize::parse(env_or("DB_POOL_SIZE", "10"))?,
            },
            server: ServerConfig {
                port: Port::parse(env_or("PORT", "8080"))?,
            },
        })
    }
}
```

### Partial updates without reintroducing invalid states

```rust
// Command carries only the fields being updated — each already parsed
pub struct UpdateOrderCommand {
    pub order_id: OrderId,
    pub new_status: Option<OrderStatus>,    // already a valid enum variant
    pub shipping: Option<ShippingAddress>,   // already parsed newtype
}

// Domain logic decides whether the transition is valid
impl Order {
    pub fn apply_update(self, cmd: UpdateOrderCommand) -> Result<Self, OrderError> {
        let status = match cmd.new_status {
            Some(new) => self.status.transition_to(new)?,  // pure validation
            None => self.status,
        };
        Ok(Self { status, ..self })
    }
}
```

---

## Type-Driven Design

### Core rules

- **Parse, don't validate.** Parse once at boundaries, trust types forever after.
- **Make illegal states unrepresentable.** Use enums with variant-specific data, not structs with optional fields.
- **Newtypes over primitives.** No raw `String`, `i64`, or `Uuid` in domain signatures.
- **Typestate for workflows.** Model state machines as generic type parameters. Invalid transitions must not compile.
- **ADTs are the modeling language.** Enums + structs replace class hierarchies.
- **Value objects over mutable entities.** State transitions return new values.

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

---

## Error Modeling

Errors are typed, layered, and never stringly typed.

### Layer separation

```rust
// domain/error.rs — business rule violations, no infrastructure concerns
#[derive(Debug, thiserror::Error)]
pub enum OrderError {
    #[error("cannot transition from {from} to {to}")]
    InvalidTransition { from: OrderStatus, to: OrderStatus },
    #[error("order total exceeds credit limit: {total} > {limit}")]
    CreditLimitExceeded { total: Money, limit: Money },
    #[error("empty order — at least one item required")]
    EmptyOrder,
}

// infrastructure/error.rs — technical failures
#[derive(Debug, thiserror::Error)]
pub enum InfraError {
    #[error("database query failed")]
    Database(#[from] sqlx::Error),
    #[error("external service unavailable: {service}")]
    ServiceDown { service: &'static str },
    #[error("data corruption in {entity}: {detail}")]
    DataCorruption { entity: &'static str, detail: String },
}

// application/error.rs — combines both layers for use-case results
#[derive(Debug, thiserror::Error)]
pub enum AppError {
    #[error(transparent)]
    Domain(#[from] OrderError),
    #[error(transparent)]
    Infra(#[from] InfraError),
    #[error(transparent)]
    Validation(#[from] ValidationError),
}
```

### Rules

| Layer          | Error type             | Crates allowed                        |
|----------------|------------------------|---------------------------------------|
| Domain         | Domain-specific enum   | `thiserror` only                      |
| Infrastructure | Infra-specific enum    | `thiserror`, wraps driver errors      |
| Application    | Composite enum         | `thiserror`, `From` impls for layers  |
| Interface      | HTTP/CLI error mapping | `thiserror` or `anyhow` (only here)   |
| `main.rs`      | Top-level              | `anyhow` / `eyre` allowed             |

- `anyhow` / `eyre` never appear in domain or infrastructure.
- Error variants carry **structured context** (types, IDs, amounts) — not format strings.
- `?` composes errors through `From` impls. Write the `From` chain explicitly.
- Domain errors are **decisions** the business cares about. Infra errors are **incidents** ops cares about.

---

## Behavior Rules

- **Tell, don't ask.** Don't inspect state then decide — give types the info they need and let them act.
- **Railway-oriented programming.** Chain operations through `Result`/`Option` pipelines with `and_then`, `map`, `map_err`.
- **Total functions.** Handle all input cases. No panics on valid input.
- **Exhaustive matching.** No `_` catch-alls unless justified (e.g., `#[non_exhaustive]` from external crates).
- **Cancellation-safe orchestration.** Treat every `await` as a cancellation point in application and infrastructure code. Use transaction boundaries, outbox patterns, and idempotent operations so cancellation never leaves partial externally visible side effects.

### Function design

- Small: one level of abstraction per function.
- Single-purpose: one reason to change.
- Return values over performing side effects.
- Closures for behavior injection by default; traits only when closures are insufficient
  (object safety needed, or the behavior has multiple methods).

### Mutation discipline

- Default to immutable. State transitions return new values.
- `mut` only when performance requires it **and** mutation is local to the function.
- Never expose `&mut self` across module boundaries without justification.
- Interior mutability (`Cell`, `RefCell`, `Mutex`) is a code smell in domain — justify every use.

---

## Dependency Injection

- Traits define **capabilities** (ports): `trait OrderRepository`, `trait PaymentGateway`.
- Concrete implementations live in `infrastructure/`.
- Application handlers receive ports as generic parameters or trait objects.
- Test doubles implement the same traits.

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
- Use domain vocabulary from the business — not programmer jargon.

---

## Pattern Palette

**Use freely:** newtypes, ADTs (enum modeling), `TryFrom`/`From` at boundaries, `Result`/`Option` pipelines, tell-don't-ask, function composition, CQRS command/query split, module facades, traits-as-capabilities, smart constructors, exhaustive matching.

**Use when justified:** typestate (3+ states, cross-module), builder (many optional params), trait-based strategy (when closures won't do — multiple methods needed), `Arc<dyn Trait>` (genuinely heterogeneous collections).

**Avoid:** Visitor (use `match`), Singleton (use DI), classic Factory (use `TryFrom`/`parse`), service objects holding domain logic, `Box<dyn Any>` downcasting, marker traits without compiler enforcement.

---

## Anti-Patterns to Reject

- `UserService` / `OrderManager` god objects accumulating domain logic.
- Raw `String`, `i64`, `Uuid` leaking through domain function signatures.
- `async fn` or IO anywhere in `domain/`.
- `Err("something went wrong".into())` — string errors.
- `_ => {}` silencing the compiler on domain enums.
- `domain/` importing from `infrastructure/` or `application/`.
- Validating the same invariant in multiple places after the boundary.
- Traits with a single implementor and no test double.
- `&mut self` as a default — justify every mutation.
- `clone()` to satisfy the borrow checker — restructure ownership instead.
- God-mode `App` or `Context` struct passed everywhere.

---

## Testing Strategy

### By layer

**Domain (unit tests — pure, fast, no mocks):**

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

**Boundaries (TryFrom tests — valid and invalid inputs):**

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

**Application (integration tests — real logic, fake infra):**

```rust
#[tokio::test]
async fn create_order_persists_and_notifies() {
    let repo = FakeOrderRepo::new();
    let notifier = FakeNotifier::new();
    let handler = CreateOrderHandler::new(repo.clone(), notifier.clone());

    let cmd = CreateOrderCommand { customer: test_customer(), items: test_items() };
    let result = handler.handle(cmd).await.unwrap();

    assert!(repo.contains(result.order_id));
    assert!(notifier.was_called_with(result.order_id));
}
```

**Property tests (for value objects and parsers):**

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

### Test naming

`<unit>_<scenario>_<expected>`: `pending_order_can_transition_to_confirmed`, `email_without_at_rejects`.

### What not to test

- Private helper functions — test through the public API.
- Framework glue (Axum route registration, serde derives) — unless custom logic is involved.
- Things the compiler already guarantees (typestate transitions that don't compile).

### Cancellation safety tests

- For each async use case, include at least one test that simulates cancellation between awaited steps.
- Assert externally observable consistency after cancellation (no partial write + notify, no duplicate side effects on retry, durable state remains valid).

```rust
#[tokio::test]
async fn create_order_is_cancellation_safe_between_persist_and_notify() {
    let repo = FakeOrderRepo::new();
    let notifier = BlockingNotifier::new(); // blocks until test releases it
    let handler = CreateOrderHandler::new(repo.clone(), notifier.clone());

    let task = tokio::spawn(handler.handle(valid_cmd()));
    notifier.wait_until_called().await; // ensure we are at a cancellation-sensitive point
    task.abort();
    let _ = task.await; // JoinError expected

    // Assert consistency after cancellation.
    // Example policy: either both persist+notify happened, or neither; retries are idempotent.
    assert!(repo.is_consistent());
    assert!(notifier.no_duplicates());
}
```

---

## Before / After: Common Refactorings

### God object → feature module with pure core

```rust
// BEFORE — everything in one place, mixed IO and logic
impl OrderService {
    async fn create_order(&self, req: CreateOrderRequest) -> Result<OrderResponse> {
        // validates input inline
        if req.items.is_empty() { return Err(anyhow!("no items")); }
        // business logic mixed with DB calls
        let total = req.items.iter().map(|i| i.price * i.qty).sum::<f64>();
        let id = sqlx::query!("INSERT INTO orders ...").execute(&self.pool).await?.last_insert_id();
        self.email_client.send_confirmation(id).await?;
        Ok(OrderResponse { id, total })
    }
}

// AFTER — separated by responsibility
// domain/order/model.rs (pure)
impl Order {
    pub fn new(items: NonEmpty<OrderItem>) -> Self { ... }
    pub fn total(&self) -> Money { self.items.iter().map(|i| i.subtotal()).sum() }
}

// domain/order/error.rs (pure)
#[derive(Debug, thiserror::Error)]
pub enum OrderError {
    #[error("empty order")]
    EmptyOrder,
}

// application/handlers.rs (orchestration)
pub async fn create_order(
    cmd: CreateOrderCommand,               // already parsed at boundary
    repo: &impl OrderRepository,
    notifier: &impl OrderNotifier,
) -> Result<OrderId, AppError> {
    let order = Order::new(cmd.items);      // pure domain
    let id = repo.save(&order).await?;      // infra via port
    notifier.order_created(id).await?;      // infra via port
    Ok(id)
}
```

### Primitive obsession → newtypes

```rust
// BEFORE — can silently swap customer_id and order_id
fn cancel_order(customer_id: i64, order_id: i64) -> Result<()> { ... }

// AFTER — compiler rejects swapped arguments
fn cancel_order(customer: CustomerId, order: OrderId) -> Result<(), OrderError> { ... }
```

### Scattered validation → parse-once boundary

```rust
// BEFORE — validates in handler, again in repo, again in model
fn handler(email: String) {
    if !email.contains('@') { panic!("bad email"); }   // handler validates
    save_user(email.clone());                           // repo validates again?
}

// AFTER — parsed once, trusted everywhere
fn handler(req: RegisterRequest) -> Result<(), AppError> {
    let cmd = RegisterCommand::try_from(req)?;  // Email::parse() happens here
    save_user(cmd.email);                       // Email type is trusted — no check
    Ok(())
}
```

---

## Tradeoff Rules

Architecture guidance that doesn't say "when not to" is dogma. Apply judgment.

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
| Introduce CQRS command/query split      | Does this use case have different read and write models? If not, overkill.|

The goal is **working software with clear boundaries** — not architectural purity for its own sake.

---

## Code Review Checklist

Before approving any change:

- [ ] Any raw `String`, `i64`, or `Uuid` in domain function signatures? → Wrap in newtype.
- [ ] Any IO or `async` in `domain/`? → Move to infrastructure.
- [ ] Any validation after the boundary (re-checking a parsed type)? → Remove.
- [ ] Any `_ => {}` on a domain enum? → Match exhaustively.
- [ ] Any trait with a single implementor and no test double? → Remove the trait.
- [ ] Any `clone()` without a justifying comment? → Restructure or comment.
- [ ] Any `unwrap()` / `expect()` outside tests? → Use `?` or handle.
- [ ] Any `anyhow` / `eyre` in domain or infrastructure? → Use typed error.
- [ ] Any `&mut self` that could be `&self` with a returned new value? → Prefer immutable.
- [ ] Any domain module importing from infrastructure? → Invert the dependency.
- [ ] Any stringly-typed error (`Err("...".into())`)? → Use a proper variant.
- [ ] Any async orchestration vulnerable to cancellation at `await` points? → Ensure transactional/idempotent behavior and no partial externally visible side effects.
- [ ] Tests cover happy path, at least one error path, and boundary parsing? → Add missing.
- [ ] For async use cases, do tests include cancellation/interruption paths? → Add at least one cancellation safety test per critical workflow.

---

## Incremental Adoption

For existing codebases, adopt this architecture incrementally:

**Phase 1 — Low effort, high payoff:**
- Introduce newtypes for IDs and validated strings at module boundaries.
- Replace `String`-based errors with typed enums in new code.
- Add `TryFrom` parsing at one external boundary (e.g., HTTP input).

**Phase 2 — Structural separation:**
- Extract pure domain logic out of handlers into standalone functions.
- Split domain types and infrastructure types into separate modules.
- Introduce port traits where test doubles would help.

**Phase 3 — Full architecture:**
- Enforce the layer dependency rules (domain imports nothing external).
- Move all IO behind port traits.
- Establish the crate layout as described above.

Each phase is independently valuable. Stop wherever the cost/benefit ratio peaks for your project.

---

## Commands

```bash
cargo build                         # compile
cargo test                          # run all tests
cargo clippy -- -D warnings         # lint — treat warnings as errors
cargo fmt --check                   # format check
```

Run `cargo clippy` and `cargo test` before considering any task complete.

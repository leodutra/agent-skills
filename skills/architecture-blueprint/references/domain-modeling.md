# Domain Modeling

Type-driven toolkit: newtypes, value objects, parse-don't-validate, illegal states, policies/specifications, rich domain objects, functional core, temporal modeling, idempotency, persistence. (Keyword conventions: see SKILL.md.)

Apply in Evolution-Path order. **Vertical slices are prioritized over rich domain objects.** Type-driven modeling (newtypes, value objects, illegal-states-unrepresentable) is on from Stage 1 and MUST NOT be deferred. Newtypes and value objects MUST live under `domain/`, not in separate technical-kind folders.

Language note: examples are TypeScript/Rust. For Python, use `typing.NewType`, frozen `@dataclass`, `Union`, `match`, and boundary parsing.

## Where behavior lives

`domain/` holds concepts, type definitions (newtypes, value objects), and invariants.

```text
domain/
├── Order
├── OrderStatus
└── OrderEvents
```

Default: behavior SHOULD live in the vertical slice, calling a functional core (pure functions on typed data). A `refund-order` slice computes via `calculateRefund(...)`; it needs no `Order` class with methods.

You SHOULD escalate to behavior-on-objects (`order.cancel()` instead of mutating state) ONLY on a trigger:

- (a) Many related rules cluster on one entity.
- (b) An invariant spans multiple operations (order total = sum of lines + tax).
- (c) Real lifecycle/state machine with illegal transitions to forbid.
- (d) Same invariant enforced from 2+ slices (centralize so copies can't drift).
- (e) High cost of violation (money, inventory, compliance).

Absent a trigger, a rich object is over-engineering. Authorization is NOT one of these invariants. "Who may act" MUST stay in a `can*` policy at use-case entry (see `authorization.md`); the entity guards ONLY business invariants.

## Newtypes — identity distinction

Wrap primitive identifiers so the compiler tells them apart. You SHOULD use a newtype whenever two values of the same primitive type could be swapped (almost always true for ids); it gives compile-time safety and prevents argument-order bugs.

```ts
type CustomerId = Brand<string, "CustomerId">
type OrderId    = Brand<string, "OrderId">
```

```rust
struct CustomerId(String);
struct OrderId(String);
```

```python
CustomerId = NewType("CustomerId", str)
OrderId    = NewType("OrderId", str)
```

## Value objects — concepts with rules

Value objects MUST be immutable, self-validating, equal by value, and behavior-rich. Use one when a concept carries validation, invariants, or behavior. Examples: `Money`, `Email`, `Percentage`, `Quantity`, `Distance`, `Duration`.

```ts
class Money {
  add(other: Money): Money
  subtract(other: Money): Money
}
```

```python
@dataclass(frozen=True)
class Money:
    amount: int
    currency: Currency
    def add(self, other: "Money") -> "Money": ...
```

Use a newtype when it only identifies; a value object when it has rules, behavior, or structure.

## Parse, don't validate

Validation MUST happen ONCE, at the boundary, converting raw input into already-valid domain types. Downstream code MUST NOT re-validate: a `Money`/`Email`/`CustomerId` is guaranteed valid by its type. You SHOULD prefer typed APIs (`refund(customerId: CustomerId, amount: Money)`) over primitives (`refund(string, number)`).

**Configuration is boundary input too.** Environment variables, files, and flags MUST be parsed ONCE at startup into a typed `Config` carrying domain types (`Port(u16)`, `DatabaseUrl`, `Timeout(Duration)`). Code MUST NOT reach for raw lookups at point of use (`env::var("PORT")`, `process.env.PORT`, `os.environ[...]`). A missing or malformed value MUST fail at startup, NOT on the first request that needs it.

**Boundary parsing SHOULD be packaged as reusable components** where the framework supports it (Axum extractors, FastAPI dependencies, middleware). The handler MUST receive already-typed values — `AuthenticatedUser`, `Tenant`, `Pagination`, `CreateOrderRequest` — never the raw transport object. Naming note: such a framework "extractor" is a `parser` in the role vocabulary; `extractor` there means pulling information out of a larger structure.

## Make illegal states unrepresentable

You SHOULD forbid invalid combinations in the type system rather than guarding at runtime. Avoid `{ status: "Shipped", shippedAt: undefined }`. Prefer a discriminated union (sum type) where each variant carries exactly its valid data:

```ts
type Order =
  | DraftOrder
  | ApprovedOrder
  | ShippedOrder   // carries a required shippedAt
```

Python: model variants as distinct frozen dataclasses combined in a `Union`, matched with `match`.

The same technique applies to **component lifecycle** (`Created → Initialized → Running → Draining → Stopped`): where the lifecycle matters, each state MAY be its own type (typestate) so that `stop()` CANNOT be called on a component that never started. Reach for typestate ONLY where an illegal transition is actually costly; elsewhere an enum plus a guard is enough.

## Error taxonomy

Errors MUST be classified by the layer that owns them. A system with one flat error type CANNOT distinguish a business outcome from an outage, and will retry the wrong things.

| Kind | Owner | Example |
| --- | --- | --- |
| Domain | `domain/` | `OrderAlreadyCancelled`, `InsufficientInventory` |
| Application | slice | `RefundNotAuthorized`, `ConcurrentUpdate` |
| Infrastructure | `gateway` / `platform/` | `DatabaseUnavailable`, `StripeTimeout` |
| Transport | edge | `InvalidJson`, `PayloadTooLarge` |

- A lower-level error MUST NOT leak outward unmapped. Infrastructure failures MUST be translated at the module boundary (`gateway`/`translator`) into a domain or application error the caller can reason about.
- Domain errors MUST be typed values, not strings, and SHOULD form an enum/union so exhaustive handling is checkable by the compiler.
- The transport edge decides status codes; the domain MUST NOT know them. `OrderAlreadyCancelled` → 409 is an edge mapping, and it MUST live at the edge.
- Expected business outcomes SHOULD be return values (`Result`, typed union), NOT exceptions or panics. Reserve unwinding for genuine faults.
- Only infrastructure errors are candidates for retry. Retrying a domain error is a defect.

## Policies vs. specifications

**Policy = the default for business decisions.** Answers "what is the rule/decision?" Bundles related decisions and calculations for one area; owns no infrastructure; pure and testable.

```ts
class RefundPolicy {
  canRefund(order: Order): boolean { ... }
  refundAmount(order: Order): Money { ... }
}
```

**Specification = a specialized tool, NOT a building block.** Answers "does this satisfy criteria?" One composable predicate (`isSatisfiedBy(x): boolean`). You SHOULD introduce a specification object ONLY when actually composing predicates (`.and()/.or()/.not()`) or driving dynamic queries (`repository.find(spec)`). Heuristic: ~10–20 policies per specification in business systems (predicate-heavy domains may run higher). Otherwise write a method/function (`customer.isEligible()`).

The `policies/` folder is NOT mandatory. Single-slice decisions SHOULD stay in the slice. The folder SHOULD emerge ONLY when decision logic is shared by 2+ slices. EXCEPTION: authorization `can*` policies MAY be grouped in `policies/` for auditability even when slice-specific (see `authorization.md`).

```text
orders/
├── domain/
├── create-order/
├── refund-order/
└── policies/        # shared by 2+ slices, or authorization can* policies
```

**Naming:** use intent-revealing names (`RefundPolicy`, `PricingPolicy`). Reactive when-then logic MUST be named **processes/handlers/reactions**, not policies.

**Toolkit summary:** newtypes = identity; value objects = concept + rules + behavior; domain objects = state + invariants (escalation only); policies = reusable decisions (default); specifications = composition/querying/qualification only.

## Functional core, imperative shell

Business logic SHOULD be pure (deterministic, side-effect-free, trivially testable): `calculateRefund(...)`, `calculateShipping(...)`. Side effects (persistence, network, clock, queues) MUST be pushed to the edges. The shell gathers inputs, calls the core, performs effects.

## Temporal modeling

Where rules depend on *when* something happened, you MUST store the timestamp explicitly (`approvedAt`, `shippedAt`, `cancelledAt`) rather than inferring it from `status`.

## Idempotency

Externally triggered commands MUST be safe to retry — executing `refundOrder()`/`createInvoice()` twice MUST NOT corrupt state or double-charge. This is REQUIRED for event handlers, queues, retries, and distributed workflows. Use idempotency keys, dedup tables, conditional writes, or equivalent controls.

## Persistence

Persistence is infrastructure and lives at the edges. You SHOULD call the ORM/query builder directly by default (`orm.orders.create(...)`). You MUST NOT add a repository by default — only for measurable value (genuine query reuse, a real planned storage swap). You MUST NOT justify a repository by testability alone or hypothetical DB swaps.

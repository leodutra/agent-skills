# Domain Modeling

Type-driven toolkit: newtypes, value objects, parse-don't-validate, illegal states, policies/specifications, rich domain objects, functional core, temporal modeling, idempotency, persistence. (Keyword conventions: see SKILL.md.)

Apply in Evolution-Path order. **Vertical slices are prioritized over rich domain objects.** Type-driven modeling (newtypes, value objects, illegal-states-unrepresentable) is on from Stage 1 and MUST NOT be deferred — it is plain data and types, independent of where behavior lives. Newtypes and value objects MUST live under `domain/`, not in separate technical-kind folders.

Language note: examples are TypeScript/Rust; Python equivalents are given inline (use `typing.NewType` for newtypes, frozen `@dataclass` for value objects, `Union` + `match` for sum types). For dynamically typed languages, enforce the same guarantees with parsing/validation at the boundary plus immutable types.

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

A method protects invariants a bare assignment CANNOT (`order.cancel()` can reject a shipped order; `order.status = "Cancelled"` cannot). Absent a trigger, a rich object is over-engineering. Authorization is NOT one of these invariants — "who may act" MUST stay in a `can*` policy at use-case entry (see `authorization.md`); the entity guards ONLY business invariants.

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

## Make illegal states unrepresentable

You SHOULD forbid invalid combinations in the type system rather than guarding at runtime. Avoid `{ status: "Shipped", shippedAt: undefined }`. Prefer a discriminated union (sum type) where each variant carries exactly its valid data:

```ts
type Order =
  | DraftOrder
  | ApprovedOrder
  | ShippedOrder   // carries a required shippedAt
```

Python: model variants as distinct frozen dataclasses combined in a `Union`, matched with `match`. If a bad state CANNOT be constructed, no code path produces it.

## Policies vs. specifications

**Policy = the default for business decisions.** Answers "what is the rule/decision?" Bundles related decisions and calculations for one area; owns no infrastructure; pure and testable.

```ts
class RefundPolicy {
  canRefund(order: Order): boolean { ... }
  refundAmount(order: Order): Money { ... }
}
```

`refundPolicy.canRefund(order)` reads clearly for humans and AI. A policy can answer several related questions about one area, which a single predicate cannot.

**Specification = a specialized tool, NOT a building block.** Answers "does this satisfy criteria?" One composable predicate (`isSatisfiedBy(x): boolean`). You SHOULD introduce a specification object ONLY when actually composing predicates (`.and()/.or()/.not()`) or driving dynamic queries (`repository.find(spec)`). Heuristic: ~10–20 policies per specification in business systems (predicate-heavy domains may run higher). Otherwise write a method/function (`customer.isEligible()`).

The `policies/` folder is NOT mandatory. Single-slice decisions SHOULD stay in the slice; the folder SHOULD emerge ONLY when decision logic is shared by 2+ slices. A folder of single-use policies is layering in disguise. EXCEPTION: authorization `can*` policies MAY be grouped in `policies/` for auditability even when slice-specific (see `authorization.md`).

```text
orders/
├── domain/
├── create-order/
├── refund-order/
└── policies/        # shared by 2+ slices, or authorization can* policies
```

**Naming:** intent-revealing (`RefundPolicy`, `PricingPolicy`). Collision warning: in event-storming, "policy" means the reactive "when X then command Y" glue (process manager). Since this architecture uses domain events, you MUST name reactive when-then logic **processes/handlers/reactions** and reserve "policy" for decisions.

**Toolkit summary:** newtypes = identity; value objects = concept + rules + behavior; domain objects = state + invariants (escalation only); policies = reusable decisions (default); specifications = composition/querying/qualification only.

## Functional core, imperative shell

Business logic SHOULD be pure (deterministic, side-effect-free, trivially testable): `calculateRefund(...)`, `calculateShipping(...)`. Side effects (persistence, network, clock, queues) MUST be pushed to the edges. The shell gathers inputs, calls the core, performs effects.

## Temporal modeling

Time is first-class. Where rules depend on *when* something happened, you MUST store the timestamp explicitly (`approvedAt`, `shippedAt`, `cancelledAt`) rather than inferring it from `status`. Temporal rules: refund windows, reservation expiration, renewals, SLAs. `status` alone CANNOT answer "delivered within 30 days?"; `deliveredAt` can.

## Idempotency

Externally triggered commands MUST be safe to retry — executing `refundOrder()`/`createInvoice()` twice MUST NOT corrupt state or double-charge. This is REQUIRED for event handlers, queues, retries, and distributed workflows. Techniques: idempotency keys, dedup tables, conditional writes. Assume any message can arrive more than once.

## Persistence

Persistence is infrastructure and lives at the edges. You SHOULD call the ORM/query builder directly by default (`orm.orders.create(...)`). You MUST NOT add a repository by default — only for measurable value (genuine query reuse, a real planned storage swap). "For testability" / "in case we swap the DB" is premature.

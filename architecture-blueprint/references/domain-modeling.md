# Domain Modeling

Type-driven toolkit: newtypes, value objects, parse-don't-validate, illegal states, policies/specifications, rich domain objects, functional core, temporal modeling, idempotency, persistence.

Apply in Evolution-Path order. **Vertical slices are prioritized over rich domain objects.** Type-driven modeling (newtypes, value objects, illegal-states-unrepresentable) is on from Stage 1 — it is plain data and types, independent of where behavior lives. **Newtypes and value objects live under `domain/`**, not in separate technical-kind folders.

## Where behavior lives

`domain/` holds concepts, type definitions (newtypes, value objects), and invariants.

```text
domain/
├── Order
├── OrderStatus
└── OrderEvents
```

**Default: behavior lives in the vertical slice**, calling a functional core (pure functions on typed data). A `refund-order` slice computes via `calculateRefund(...)`; it needs no `Order` class with methods.

**Escalate to behavior-on-objects** (`order.cancel()` instead of mutating state) only on a trigger:

- (a) Many related rules cluster on one entity.
- (b) An invariant spans multiple operations (order total = sum of lines + tax).
- (c) Real lifecycle/state machine with illegal transitions to forbid.
- (d) Same invariant enforced from 2+ slices (centralize so copies can't drift).
- (e) High cost of violation (money, inventory, compliance).

A method protects invariants a bare assignment cannot (`order.cancel()` can reject a shipped order; `order.status = "Cancelled"` cannot). Absent a trigger, a rich object is over-engineering. Authorization is **not** one of these invariants — keep "who may act" in a `can*` policy at use-case entry (see `authorization.md`); the entity guards only business invariants.

## Newtypes — identity distinction

Wrap primitive identifiers so the compiler tells them apart.

```ts
type CustomerId = Brand<string, "CustomerId">
type OrderId    = Brand<string, "OrderId">
```

```rust
struct CustomerId(String);
struct OrderId(String);
```

Use whenever two values of the same primitive type could be swapped (almost always true for ids). Gives compile-time safety and prevents argument-order bugs.

## Value objects — concepts with rules

Immutable, self-validating, equality by value, behavior-rich. Use when a concept carries validation, invariants, or behavior. Examples: `Money`, `Email`, `Percentage`, `Quantity`, `Distance`, `Duration`.

```ts
class Money {
  add(other: Money): Money
  subtract(other: Money): Money
}
```

Newtype when it only identifies; value object when it has rules, behavior, or structure.

## Parse, don't validate

Validate **once** at the boundary, converting raw input into already-valid domain types. Downstream, a `Money`/`Email`/`CustomerId` is guaranteed valid — no re-checking. Prefer typed APIs (`refund(customerId: CustomerId, amount: Money)`) over primitives (`refund(string, number)`).

## Make illegal states unrepresentable

Forbid invalid combinations in the type system, not at runtime. Avoid `{ status: "Shipped", shippedAt: undefined }`. Prefer a discriminated union (sum type) where each variant carries exactly its valid data:

```ts
type Order =
  | DraftOrder
  | ApprovedOrder
  | ShippedOrder   // carries a required shippedAt
```

If a bad state can't be constructed, no code path produces it.

## Policies vs. specifications

**Policy = the default for business decisions.** Answers "what is the rule/decision?" Bundles related decisions and calculations for one area; owns no infrastructure; pure and testable.

```ts
class RefundPolicy {
  canRefund(order: Order): boolean { ... }
  refundAmount(order: Order): Money { ... }
}
```

`refundPolicy.canRefund(order)` reads clearly for humans and AI. A policy can answer several related questions about one area, which a single predicate cannot.

**Specification = a specialized tool, not a building block.** Answers "does this satisfy criteria?" One composable predicate (`isSatisfiedBy(x): boolean`). Earns its place **only** when you actually compose predicates (`.and()/.or()/.not()`) or drive dynamic queries (`repository.find(spec)`). Heuristic: ~10–20 policies per specification in business systems (predicate-heavy domains may run higher). Otherwise write a method/function (`customer.isEligible()`).

**`policies/` folder is not mandatory.** Single-slice decisions stay in the slice; the folder emerges only when decision logic is shared by 2+ slices. A folder of single-use policies is layering in disguise. (Exception: authorization `can*` policies may be grouped in `policies/` for auditability even when slice-specific — see `authorization.md`.)

```text
orders/
├── domain/
├── create-order/
├── refund-order/
└── policies/        # only when shared by 2+ slices
```

**Naming:** intent-revealing (`RefundPolicy`, `PricingPolicy`). Collision warning: in event-storming, "policy" means the reactive "when X then command Y" glue (process manager). Since this architecture uses domain events, name reactive when-then logic **processes/handlers/reactions** — reserve "policy" for decisions.

**Toolkit summary:** newtypes = identity; value objects = concept + rules + behavior; domain objects = state + invariants (escalation only); policies = reusable decisions (default); specifications = composition/querying/qualification only.

## Functional core, imperative shell

Keep business logic pure (deterministic, side-effect-free, trivially testable): `calculateRefund(...)`, `calculateShipping(...)`. Push side effects (persistence, network, clock, queues) to the edges. The shell gathers inputs, calls the core, performs effects.

## Temporal modeling

Time is first-class. Store timestamps explicitly where rules depend on *when* (`approvedAt`, `shippedAt`, `cancelledAt`) rather than inferring from `status`. Temporal rules: refund windows, reservation expiration, renewals, SLAs. `status` alone can't answer "delivered within 30 days?"; `deliveredAt` can.

## Idempotency

Externally triggered commands must be safe to retry — executing `refundOrder()`/`createInvoice()` twice must not corrupt state or double-charge. Required for event handlers, queues, retries, distributed workflows. Techniques: idempotency keys, dedup tables, conditional writes. Assume any message can arrive more than once.

## Persistence

Infrastructure, at the edges. Calling the ORM/query builder directly is the default (`orm.orders.create(...)`). Do **not** add a repository by default — only for measurable value (genuine query reuse, a real planned storage swap). "For testability" / "in case we swap the DB" is premature.

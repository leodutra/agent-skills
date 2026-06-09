# Domain Modeling

The type-driven toolkit for modeling a business domain: newtypes, value objects, parse-don't-validate, illegal states, policies, rich domain objects, functional core, temporal modeling, idempotency, and persistence. Read this when modeling concepts or reviewing how a domain is expressed.

Apply these in the order of the Evolution Path, and remember this blueprint prioritizes **vertical slices over rich domain objects**: newtypes and parse-don't-validate first (Stage 1), value objects and shared decision logic next (Stage 2), and behavior-on-objects only as an escalation (Stage 3) when specific triggers fire. Type-driven modeling (newtypes, value objects, illegal-states-unrepresentable) is *not* an escalation — keep it on from the start; it's plain data and types, independent of where behavior lives.

**Newtypes and value objects live under `domain/`** (see `structure-and-boundaries.md`), not in separate technical-kind folders.

## Domain layer and where behavior lives

The domain layer holds business concepts, the type definitions (newtypes, value objects), and the invariants that protect them.

```text
domain/
├── Order.ts          # concept + newtypes + value objects for orders
├── OrderStatus.ts
└── OrderEvents.ts
```

**By default, behavior lives in the vertical slice that uses it**, calling a functional core (pure functions on typed data) — not on rich domain objects. A `refund-order` slice computes the refund with `calculateRefund(...)` and writes the result; it does not require an `Order` class with methods.

**Escalate to behavior-on-objects** — `order.cancel()` rather than mutating state in the slice — only when a concrete trigger fires:

- **(a) Clustered rules:** many related business rules accrete on one entity.
- **(b) Cross-operation invariant:** an invariant must hold across several operations (order total = sum of lines + tax), and you don't want each slice re-deriving it.
- **(c) Lifecycle / state machine:** the entity has a real lifecycle (draft → approved → shipped) with transitions that must be forbidden when invalid.
- **(d) Duplicated invariant:** the same rule is already enforced from 2+ slices — centralize it on the object so the copies can't drift.
- **(e) High cost of violation:** money, inventory, or compliance, where a single missed guard is expensive.

When you do escalate, the reason a method beats a bare assignment is that a method can check preconditions and preserve invariants ("a shipped order cannot be cancelled"); `order.status = "Cancelled"` cannot. Behavior is where invariants are defended — but only centralize that behavior once an entity earns it. Absent a trigger, a rich object is over-engineering; keep the logic in the slice.

## Newtypes — type distinction for identity

Wrap primitive identifiers so the compiler can tell them apart.

```ts
type CustomerId = Brand<string, "CustomerId">
type OrderId    = Brand<string, "OrderId">
```

```rust
struct CustomerId(String);
struct OrderId(String);
```

This gives compile-time safety (you cannot pass an `OrderId` where a `CustomerId` is expected), semantic clarity, and prevention of argument-order bugs. Use a newtype whenever two values of the same primitive type could be confused — which is almost always true for ids.

## Value objects — concepts with rules

A value object represents a concept that carries validation, invariants, or behavior. Examples: `Money`, `Email`, `Percentage`, `Quantity`, `Distance`, `Weight`, `Duration`, `Currency`.

Properties: immutable, self-validating, equality by value, behavior-rich.

```ts
class Money {
  add(other: Money): Money
  subtract(other: Money): Money
}
```

Use a value object (rather than a newtype) when the concept does more than identify — when it has rules (a percentage is 0–100), behavior (money adds), or composite structure.

## Parse, don't validate

Validate **once**, at the system boundary, and convert raw input into already-valid domain types. After that point, a `Money`, `Email`, or `CustomerId` is *guaranteed* valid — no function downstream needs to re-check it.

Prefer typed APIs:

```ts
refund(customerId: CustomerId, amount: Money)
```

over primitive-based APIs (`refund(customerId: string, amount: number)`), which force every caller to wonder whether the values were checked. Parsing pushes validation to the edge and lets the type system carry the guarantee inward.

## Make illegal states unrepresentable

Use the type system to forbid invalid combinations rather than guarding against them at runtime.

Avoid a shape where invalid combinations are expressible:

```ts
{ status: "Shipped", shippedAt: undefined }   // shipped with no ship date?
```

Prefer a discriminated union (sum type) where each variant carries exactly the data valid for that state:

```ts
type Order =
  | DraftOrder
  | ApprovedOrder
  | ShippedOrder   // ShippedOrder has a required shippedAt
```

If a bad state cannot be constructed, no code path can produce it and no test needs to cover it.

## Policies vs. specifications — the 2026 position

This architecture treats **Policy as the default first-class concept for business decisions**, and **Specification as a specialized tool** — not a foundational building block. The two answer genuinely different questions; the choice is not about taste but about which problem you have.

**A Policy answers: "what is the business rule or decision?"** It bundles the related decisions and calculations for one decision area:

```ts
class RefundPolicy {
  canRefund(order: Order): boolean { ... }
  refundAmount(order: Order): Money { ... }
}
```

Its focus is business decision, behavior, and rules. It owns no infrastructure (no DB, no HTTP) — keep it a pure decision unit so it stays testable. Crucially, a single policy can answer several related questions about one area (`canRefund` *and* `refundAmount`), which a single predicate cannot.

**A Specification answers: "does this object satisfy some criteria?"** It is one composable predicate:

```ts
class RefundableOrderSpecification {
  isSatisfiedBy(order: Order): boolean {
    return order.status === "Delivered" && order.daysSinceDelivery < 30
  }
}
```

Its focus is predicate, criteria, qualification.

**Why Policy is the default.** `refundPolicy.canRefund(order)` reads immediately to both humans and AI — and this blueprint optimizes for business language and AI readability over classical tactical-DDD patterns. The original Specification pattern, by contrast, became overloaded by years of misuse: codebases accreted `ActiveCustomerSpecification`, `EligibleCustomerSpecification`, `VerifiedCustomerSpecification`… composed into `.and().and()` chains that read worse than a plain `customer.isEligible()` or `customerPolicy.canPurchase(...)`.

**When a specification genuinely earns its place.** Only when you actually need: composable predicates, complex or dynamic querying (a spec that translates to a SQL `where` clause via `repository.find(spec)`), or reusable qualification logic. That is the use case Evans targeted — and in typical business systems it is rare. A useful (domain-dependent) heuristic: **expect roughly 10–20 policies for every 1 specification.** Predicate-heavy domains can run higher on specifications — e.g., an RTS evaluating `DeployableUnitSpecification`/`TargetVisibleSpecification` over many units — but a billing or orders system rarely does. If you reach for a specification object without actually composing or querying with it, write a method or function instead (`customer.isEligible()`).

**The `policies/` folder is not mandatory.** Decision logic used by a single slice stays *in that slice*. A `policies/` folder emerges only when reusable decision logic shared by 2+ slices appears:

```text
orders/
├── domain/          # concepts, newtypes, value objects
├── create-order/
├── refund-order/
└── policies/        # appears only when shared decision logic emerges
```

A `policies/` folder full of single-use classes is just layering in disguise.

**Naming caveat.** Prefer intent-revealing names (`RefundPolicy`, `PricingPolicy`, `PromotionPolicy`, `CreditPolicy`). Note one collision: in event-storming vocabulary, "policy" means the *reactive* "**when** OrderPaid **then** reserve inventory" glue (a process manager). Since this architecture uses domain events, name reactive when-then logic as **processes / handlers / reactions**, not policies — reserve "policy" for decision logic.

**Summary of the toolkit:** newtypes for identity (`CustomerId`, `OrderId`); value objects for concept + invariants + behavior (`Money`, `Email`, `Percentage`); domain objects for state + invariants (`Order`, `Invoice`, `Shipment`) — escalated to per the triggers above; **policies** for reusable business decisions (the default); **specifications** only when composable predicates, querying, or qualification logic genuinely demand them.

## Functional core, imperative shell

Keep business logic pure whenever possible. Pure functions are deterministic, side-effect-free, and trivial to test.

```ts
calculateRefund(...)
calculateShipping(...)
calculatePromotion(...)
```

Push side effects — persistence, network, clock, queues — to the edges (the imperative shell). The shell gathers inputs, calls the pure core, and performs the resulting effects. This keeps the hard-to-test parts thin and the business rules easy to test exhaustively.

## Temporal modeling

Treat time as a first-class domain concern. Where business rules depend on *when* something happened, store the timestamp explicitly rather than inferring it from a single `status`.

```ts
approvedAt
shippedAt
cancelledAt
```

Many rules are inherently temporal — refund windows, reservation expiration, subscription renewal, SLA enforcement. A lone `status` field cannot answer "was this delivered within 30 days?"; an explicit `deliveredAt` can.

## Idempotency

Make externally triggered commands safe to retry. Executing `approveOrder()`, `refundOrder()`, or `createInvoice()` twice must not corrupt state or double-charge.

Idempotency is required wherever delivery can repeat: event handlers, queues, retries, and distributed workflows. Typical techniques include idempotency keys, dedup tables, and conditional writes. Assume any message can arrive more than once.

## Persistence

Persistence is infrastructure and lives at the edges. Calling the ORM or query builder directly is acceptable and is the default:

```text
orm.orders.create(...)
```

Do **not** introduce a repository layer by default. A repository is justified only when it provides measurable value — genuine query reuse, or a real (not hypothetical) need to abstract storage. Adding repositories "for testability" or "in case we swap the DB" is usually premature; the cost is real and the benefit usually never materializes.

# Domain Modeling

Type-driven toolkit: newtypes, value objects, parse-don't-validate, illegal states, error taxonomy, policies/specifications, rich domain objects, functional core, temporal modeling, idempotency, persistence. (Keyword conventions: see SKILL.md. Tags `(n)` name the deriving principle in `first-principles.md`; `(ledger)` its pattern-ledger entry.)

Apply in Evolution-Path order. **Vertical slices are prioritized over rich domain objects.** Type-driven modeling (newtypes, value objects, illegal-states-unrepresentable) is on from Stage 1 and MUST NOT be deferred: it pays obligations in the cheapest currency there is — by the machine, at construction, once (frame, rung 1). Newtypes and value objects live under `domain/`, not in separate technical-kind folders (*convention* on the folder name; the derived part is "never by technical kind", 13).

Language note: examples are TypeScript/Rust. For Python, use `typing.NewType`, frozen `@dataclass`, `Union`, `match`, and boundary parsing.

## Where behavior lives

`domain/` holds concepts, type definitions (newtypes, value objects), and invariants.

```text
domain/
├── Order
├── OrderStatus
└── OrderEvents
```

Default: behavior SHOULD live in the vertical slice, calling a functional core (pure functions on typed data) (13, 14). A `refund-order` slice computes via `calculateRefund(...)`; it needs no `Order` class with methods.

You SHOULD escalate to behavior-on-objects (`order.cancel()` instead of mutating state) ONLY on a trigger:

- (a) Many related rules cluster on one entity (13 — couple by shared reason for change).
- (b) An invariant spans multiple operations (order total = sum of lines + tax) (11 — the object is the invariant's consistency scope; ledger: aggregate).
- (c) Real lifecycle/state machine with illegal transitions to forbid (4, 12 — typestate).
- (d) Same invariant enforced from 2+ slices (6 — one authoritative home, so copies cannot drift; decisions live with the authority over their subject).
- (e) High cost of violation (money, inventory, compliance) (frame — the chosen currency must *reliably* discharge the obligation; where a miss is costly, only structure is reliable enough).

Absent a trigger, a rich object is over-engineering. When trigger (b) fires, the object MUST be drawn no larger than its invariants demand (11 — every fact added taxes every change within); an object that swallows a whole module to guard one invariant is the scope drawn wrong. Authorization is NOT one of these invariants. "Who may act" MUST stay in a `can*` policy at use-case entry (see `authorization.md`); the entity guards ONLY business invariants.

## Newtypes — identity distinction

(3; ledger: semantic newtype, phantom type) Wrap primitive identifiers so the compiler tells them apart. You SHOULD use a newtype whenever two values of the same primitive type could be swapped (almost always true for ids): a distinction correctness turns on moves from naming convention into the medium, at zero runtime cost. The contrapositive binds too (3): a distinction with no consequence for correctness does not earn a newtype.

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

(1, 4; ledger: value object; 6 — immutable by default) Value objects MUST be immutable, self-validating, and equal by value, and they carry the concept's own operations where it has any (`Money.add`). Use one when a concept carries validation, invariants, or behavior: jointly-meaningful facts travel in one receipt, so their relationship is never reconstructed at use sites. Examples: `Money`, `Email`, `Percentage`, `Quantity`, `Distance`, `Duration`.

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

(1; ledger: parse don't validate, smart constructor) Validation MUST happen ONCE, at the boundary, converting raw input into already-valid domain types — establishing a fact MUST change the representation, or the obligation regenerates at every use site. Downstream code MUST NOT re-validate: a `Money`/`Email`/`CustomerId` is guaranteed valid by its type. You SHOULD prefer typed APIs (`refund(customerId: CustomerId, amount: Money)`) over primitives (`refund(string, number)`).

**Construction is the only path to possession** (1). The parsing function MUST be the only way to obtain the type (private constructor, smart constructor, sealed module); a receipt obtainable without the proof is forged. A check that returns a boolean and passes the raw value on has established nothing for anyone downstream — it is the canonical wrong-currency payment (frame).

**Do not decay a strong representation casually** (1). Unwrapping a newtype to pass the primitive inward re-creates every obligation the parse discharged. Unwrap at a frame boundary — serialization, the store, the wire — never for convenience.

**Structural reconstruction is not semantic proof** (2; ledger: DTO → domain translation). Deserializing a wire form proves syntax only. The domain's propositions are a second frame, entered by its own parse: transport DTO → domain type is a step, never an identity.

**Configuration is boundary input too** (7, 8, 1; ledger: configuration as parsed input, fail-fast startup). Environment variables, files, and flags MUST be parsed ONCE at startup into a typed `Config` carrying domain types (`Port(u16)`, `DatabaseUrl`, `Timeout(Duration)`). Code MUST NOT reach for raw lookups at point of use (`env::var("PORT")`, `process.env.PORT`, `os.environ[...]`). A missing or malformed value MUST fail at startup, NOT on the first request that needs it — viability is resolved at the threshold, not in the interior.

**Boundary parsing SHOULD be packaged as reusable components** (8, 14; ledger: middleware pipeline) where the framework supports it (Axum extractors, FastAPI dependencies, middleware). The handler MUST receive already-typed values — `AuthenticatedUser`, `Tenant`, `Pagination`, `CreateOrderRequest` — never the raw transport object. Naming note: such a framework "extractor" is a `parser` in the role vocabulary; `extractor` there means pulling information out of a larger structure.

**Inside a frame, never require the same proof twice; at a crossing, require it again** (1, 2). Re-checking a `CustomerId` inside the module is waste. Re-parsing it when it comes back from a queue, a cache, a file, or another process is not: trust follows custody, and data that left and returned has crossed a frame even if it "was yours".

## Make illegal states unrepresentable

(4; ledger) You SHOULD forbid invalid combinations in the type system rather than guarding at runtime: a case that cannot be constructed needs no test, no branch, and no memory. Avoid `{ status: "Shipped", shippedAt: undefined }`. Prefer a discriminated union (sum type) where each variant carries exactly its valid data:

```ts
type Order =
  | DraftOrder
  | ApprovedOrder
  | ShippedOrder   // carries a required shippedAt
```

Python: model variants as distinct frozen dataclasses combined in a `Union`, matched with `match`.

Principle 4 closes the gap from both sides; each of these is a MUST where correctness turns on it:

- **Mutual exclusivity is an alternative, not a conjunction.** States that exclude each other are variants of one sum type, not independent flags (`isShipped`, `isCancelled`) that manufacture 2ⁿ representable worlds for *k* meaningful ones.
- **Absence is a state, not a hole.** "Not yet," "not applicable," and "unknown" are meaningful situations, modeled as such (a variant, or an `Option`/`undefined` with one stated meaning) — NOT as sentinels (`-1`, `""`, `0`, `1970-01-01`) or an overloaded member.
- **Exhaustiveness is checkable.** Sum types are closed (sealed / `enum` / discriminated union) and matched exhaustively, so adding a variant redistributes obligations through compiler errors rather than silently creating unhandled worlds.
- **Do not compress below the domain's variety.** A representation smaller than the situation space it must express evicts the difference into convention; two real situations collapsed into one variant reappear as a comment and a bug.

The same technique applies to **component lifecycle** (`Created → Initialized → Running → Draining → Stopped`) (4, 12; ledger: typestate): where the lifecycle matters, each state MAY be its own type so that `stop()` CANNOT be called on a component that never started. Reach for typestate ONLY where an illegal transition is actually costly; elsewhere an enum plus a guard is enough.

## Error taxonomy

(9, 3; ledger: typed errors, error translation per boundary) Errors MUST be classified by the layer that owns them. A system with one flat error type CANNOT distinguish a business outcome from an outage, and will retry the wrong things. A failure is information with a frame: propagated raw across frames it leaks mechanism; swallowed, it destroys evidence. Handling is translation. The four kinds below are this skill's partition (*convention*); what 9 derives is that distinct meanings of failure get distinct representations.

| Kind | Owner | Example |
| --- | --- | --- |
| Domain | `domain/` | `OrderAlreadyCancelled`, `InsufficientInventory` |
| Application | slice | `RefundNotAuthorized`, `ConcurrentUpdate` |
| Infrastructure | `gateway` / `platform/` | `DatabaseUnavailable`, `StripeTimeout` |
| Transport | edge | `InvalidJson`, `PayloadTooLarge` |

- A lower-level error MUST NOT leak outward unmapped. Infrastructure failures MUST be translated at the module boundary (`gateway`/`translator`) into a domain or application error the caller can reason about — no richer and no poorer than what it can act on.
- Failure belongs in the contract (7 applied to outcomes): an operation that can fail and is presented as one that cannot has a hidden output.
- Domain errors MUST be typed values, not strings, and SHOULD form an enum/union so exhaustive handling is checkable by the compiler.
- The transport edge decides status codes; the domain MUST NOT know them. `OrderAlreadyCancelled` → 409 is an edge mapping, and it MUST live at the edge.
- Expected business outcomes SHOULD be return values (`Result`, typed union), NOT exceptions or panics. Reserve unwinding for genuine faults.
- Handle where understanding lives: the frame that can tell retry from refusal from redesign decides. Only infrastructure errors are candidates for retry; retrying a domain error is a defect.
- A failure's audience includes the future: translation MUST preserve the causal trail (source/cause chain, correlation ID) rather than tidy it away.

## Policies vs. specifications

(6 — one authoritative home per piece of knowledge; 1 — a stored decision beats a repeated decision) **Policy = the default for business decisions.** Answers "what is the rule/decision?" Bundles related decisions and calculations for one area; owns no infrastructure; pure and testable. `can*` names are reserved for authorization (`authorization.md`); business eligibility reads `isRefundable`, `isEligible`.

```ts
class RefundPolicy {
  isRefundable(order: Order): boolean { ... }
  refundAmount(order: Order): Money { ... }
}
```

A blueprint policy is a *stored decision* with one home. The ledger's "strategy / policy object" (13, 7) is a different thing — a *varying* policy injected as an input — and a policy becomes one ONLY when it genuinely varies per deployment, tenant, or configuration.

**Specification = a specialized tool, NOT a building block** (5 — indirection is an edge, not a virtue). Answers "does this satisfy criteria?" One composable predicate (`isSatisfiedBy(x): boolean`). You SHOULD introduce a specification object ONLY when actually composing predicates (`.and()/.or()/.not()`) or driving dynamic queries (`repository.find(spec)`). Heuristic: ~10–20 policies per specification in business systems (predicate-heavy domains may run higher). Otherwise write a method/function (`customer.isEligible()`).

The `policies/` folder is NOT mandatory. Single-slice decisions SHOULD stay in the slice. The folder SHOULD emerge ONLY when decision logic is shared by 2+ slices (6 — one home the moment a second copy would exist). EXCEPTION: authorization `can*` policies MAY be grouped in `policies/` for auditability even when slice-specific (see `authorization.md`).

```text
orders/
├── domain/
├── create-order/
├── refund-order/
└── policies/        # shared by 2+ slices, or authorization can* policies
```

**Naming:** use intent-revealing names (`RefundPolicy`, `PricingPolicy`). Reactive when-then logic is named **process/handler/reaction**, never policy (*convention*, motivated by 3 — different meanings, different names).

**Toolkit summary:** newtypes = identity; value objects = concept + rules + behavior; domain objects = state + invariants (escalation only); policies = reusable decisions (default); specifications = composition/querying/qualification only.

## Functional core, imperative shell

(7, 8; ledger) Business logic SHOULD be pure (deterministic, side-effect-free, trivially testable): `calculateRefund(...)`, `calculateShipping(...)`. Side effects (persistence, network, clock, queues) MUST be pushed to the edges. The shell gathers inputs, calls the core, performs effects — calculation separated from the world's cooperation, so the core's proofs never include the network.

**Time and chance are inputs** (7; ledger: explicit clock / injected randomness). The core MUST receive `now` (or a clock) and any random source as parameters. A function that reads the wall clock has a domain its signature does not declare, and CANNOT be replayed or tested at a chosen instant. Identity, permission, locale, and configuration are inputs the same way (see `authorization.md` and typed config above). Determinism is the default; nondeterminism is a declared dependency.

## Temporal modeling

(1, 2, 4) Where rules depend on *when* something happened, you MUST store the timestamp explicitly (`approvedAt`, `shippedAt`, `cancelledAt`) rather than inferring it from `status`: an instant of proof is part of the proof. A timestamp that may be absent is a state, not a hole (4) — a variant that carries it when it exists beats an optional field every reader must reason about. Facts with temporal scope (leases, validity windows, tokens, cached permissions) MUST carry their expiry (2 — the clock is a frame).

## Idempotency

(10; ledger: idempotency key, deduplication / inbox) Externally triggered commands MUST be safe to retry — executing `refundOrder()`/`createInvoice()` twice MUST NOT corrupt state or double-charge. This MUST hold for event handlers, queues, retries, and distributed workflows. Use idempotency keys, dedup tables, conditional writes, or equivalent controls. The key identifies the *intent*, not the message (10 — identity of intent): two arrivals of one intention MUST be recognizable as one. Where the environment genuinely guarantees exactly-once, ordered execution (one local transaction), relying on it is legitimate and cheaper; paying the idempotency price anyway is insurance, judged like any other (13).

## Persistence

(6 — localized persistence authority; 7, 8 — the world stays at the rim; 2 — trust follows custody; ledger: repository, conditional) Persistence is infrastructure and lives in the imperative shell; the functional core never touches it. The shell reaches persistence through the narrowest capability it names — `loadOrder`, `saveOrder` — which at Stage 1 is a plain function calling the ORM/query builder directly (`orm.orders.create(...)`), built where the ORM handle lives (the module's wiring) and handed in (see Capability-oriented dependencies in `structure-and-boundaries.md`; the file holding those functions is the `store` role). No repository object stands between that function and the ORM. A repository is one implementation of localized persistence authority; introduce one ONLY when it models a domain persistence boundary — aggregate-shaped load/save with rules of its own, query reuse across slices, a real planned storage swap — never one per table, and never as a grander name for the plain function. Data returning from the store has crossed a frame (2): rows are parsed into domain types at the persistence edge, not trusted because "we wrote them".

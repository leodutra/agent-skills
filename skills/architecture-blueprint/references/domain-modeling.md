# Domain Modeling

The type-driven toolkit, and where behavior lives. (Keywords and the `(n)` / `(frame)` / `(ledger)` tags: see SKILL.md.)

Type-driven modeling is on from Stage 1 because it pays obligations in the cheapest currency there is — by the machine, at construction, once (frame, rung 1).

Examples are TypeScript/Rust/Python. Python equivalents: `typing.NewType`, frozen `@dataclass`, `Union`, `match`, and boundary parsing.

## Where behavior lives

`domain/` is a vocabulary, not a layer: it holds concepts, type definitions (newtypes, value objects), and invariants (`Order`, `OrderStatus`, `OrderEvents`).

Default: behavior SHOULD live in the vertical slice, calling a functional core (pure functions on typed data) (13, 14). A `refund-order` slice computes via `calculateRefund(...)`; it needs no `Order` class with methods.

Behavior moves onto an object (`order.cancel()`) ONLY on one of SKILL.md's triggers (a)–(e). Under (b), an object that swallows a whole module to guard one invariant is the scope drawn wrong (11 — every fact added taxes every change within).

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

An identity newtype carries no invariant, so it needs no parse and MAY expose its value (1, 3). A value object carries one, so it keeps its representation private and every way in goes through its parse (see Parse, don't validate).

## Value objects — concepts with rules

(1, 4; ledger: value object; 6 — immutable by default) Value objects MUST be immutable, self-validating, and equal by value, and they carry the concept's own operations where it has any (`Money.add`). Use one when a concept carries validation, invariants, or behavior: jointly-meaningful facts travel in one receipt, so their relationship is never reconstructed at use sites. Examples: `Money`, `Email`, `Percentage`, `Quantity`, `Distance`, `Duration`.

- **Normalize at construction** (4, 1). The parse normalizes to the canonical form the domain defines (trimmed, canonical case, one unit), so equality by value compares canonical values. It MUST NOT collapse a distinction the domain keeps: an email's local part keeps its case. Normalization is idempotent, so the re-parse at a crossing is stable; `parse(format(x)) = x` is the round-trip law in `testing-and-governance.md`.
- **No default that skips the parse** (1, 4). A default, empty, or zero instance MUST NOT exist unless it is a valid value; otherwise it is a way in without the proof.
- **Immutable all the way down** (6; ledger: immutability by default). Immutability covers what the value holds: a frozen record holding a mutable list is not immutable.

## Parse, don't validate

(1; ledger: parse don't validate, smart constructor) Validation MUST happen ONCE, at the boundary, converting raw input into already-valid domain types — establishing a fact MUST change the representation, or the obligation regenerates at every use site. Downstream code MUST NOT re-validate: a `Money`/`Email`/`CustomerId` is guaranteed valid by its type. You SHOULD prefer typed APIs (`refund(customerId: CustomerId, amount: Money)`) over primitives (`refund(string, number)`).

**Every way in is the parse** (1, 6; ledger: smart constructor). For a type with an invariant, the parsing function MUST be the only way to obtain it (private constructor, smart constructor, sealed module); deserializers, config binders, CLI parsers, and framework extractors delegate to it, so the rule has one home. A deserializer that fills fields directly, a cast, or a default builds the value without the proof — a forged receipt: `JSON.parse(body) as Email` (TypeScript), `Email.model_construct(...)` (pydantic), a derived deserializer. A check that returns a boolean and passes the raw value on has established nothing downstream — the canonical wrong-currency payment (frame).

**Do not decay a strong representation casually** (1). Unwrapping a newtype to pass the primitive inward re-creates every obligation the parse discharged. Unwrap at a frame boundary — serialization, the store, the wire — never for convenience.

**Structural reconstruction is not semantic proof** (2; ledger: DTO → domain translation). Deserializing a wire form proves syntax only. The domain's propositions are a second frame, entered by its own parse: transport DTO → domain type is a step, never an identity.

**Configuration is boundary input too** (7, 8, 1; ledger: configuration as parsed input, fail-fast startup). Environment variables, files, and flags MUST be parsed ONCE at startup into a typed `Config` carrying domain types (`Port`, `DatabaseUrl`, `Timeout`). Code MUST NOT reach for raw lookups at point of use (`env::var("PORT")`, `process.env.PORT`, `os.environ[...]`). A missing or malformed value MUST fail at startup, NOT on the first request that needs it — viability is resolved at the threshold, not in the interior.

**Boundary parsing SHOULD be packaged as reusable components** (8, 14; ledger: middleware pipeline) where the framework supports it (Axum extractors, FastAPI dependencies, middleware). The handler MUST receive already-typed values — `AuthenticatedUser`, `Tenant`, `Pagination`, `CreateOrderRequest` — never the raw transport object. Naming note: such a framework "extractor" is a `parser` in `role-vocabulary.md`; `extractor` there means pulling information out of a larger structure.

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

(6 — one authoritative home per piece of knowledge; 1 — a stored decision beats a repeated decision) **Policy = the default for business decisions.** Answers "what is the rule/decision?" Bundles related decisions and calculations for one area; owns no infrastructure; pure and testable.

```ts
class RefundPolicy {
  isRefundable(order: Order): boolean { ... }
  refundAmount(order: Order): Money { ... }
}
```

A blueprint policy is a *stored decision* with one home. The ledger's "strategy / policy object" (13, 7) is a different thing — a *varying* policy injected as an input — and a policy becomes one ONLY when it genuinely varies per deployment, tenant, or configuration.

**Specification = a specialized tool, NOT a building block** (5 — indirection is an edge, not a virtue). Answers "does this satisfy criteria?" One composable predicate (`isSatisfiedBy(x): boolean`). You SHOULD introduce a specification object ONLY when actually composing predicates (`.and()/.or()/.not()`) or driving dynamic queries (`repository.find(spec)`). Heuristic: ~10–20 policies per specification in business systems (predicate-heavy domains may run higher). Otherwise write a method/function (`customer.isEligible()`).

**Naming:** use intent-revealing names (`RefundPolicy`, `PricingPolicy`). Reactive when-then logic is named **process/handler/reaction**, never policy (*convention*, motivated by 3 — different meanings, different names).

## Functional core, imperative shell

(7, 8; ledger) Business logic SHOULD be pure (deterministic, side-effect-free, trivially testable): `calculateRefund(...)`, `calculateShipping(...)`. Side effects (persistence, network, clock, queues) MUST be pushed to the edges. The shell gathers inputs, calls the core, performs effects — calculation separated from the world's cooperation, so the core's proofs never include the network.

**Time and chance are inputs** (7; ledger: explicit clock / injected randomness). The core MUST receive `now` (or a clock) and any random source as parameters. A function that reads the wall clock has a domain its signature does not declare, and CANNOT be replayed or tested at a chosen instant. Identity, permission, locale, and configuration are inputs the same way (see `authorization.md` and typed config above). Determinism is the default; nondeterminism is a declared dependency.

## Temporal modeling

(1, 2, 4) Where rules depend on *when* something happened, you MUST store the timestamp explicitly (`approvedAt`, `shippedAt`, `cancelledAt`) rather than inferring it from `status`: an instant of proof is part of the proof. A timestamp that may be absent is a state, not a hole (4) — a variant that carries it when it exists beats an optional field every reader must reason about. Facts with temporal scope (leases, validity windows, tokens, cached permissions) MUST carry their expiry (2 — the clock is a frame).

## Idempotency

(10; ledger: idempotency key, deduplication / inbox) Externally triggered commands MUST be safe to retry — executing `refundOrder()`/`createInvoice()` twice MUST NOT corrupt state or double-charge. This MUST hold for event handlers, queues, retries, and distributed workflows. Use idempotency keys, dedup tables, conditional writes, or equivalent controls. The key identifies the *intent*, not the message (10 — identity of intent): two arrivals of one intention MUST be recognizable as one. Where the environment genuinely guarantees exactly-once, ordered execution (one local transaction), relying on it is legitimate and cheaper; paying the idempotency price anyway is insurance, judged like any other (13).

## Persistence

(6 — localized persistence authority; 7, 8 — the world stays at the rim; 2 — trust follows custody; ledger: repository, conditional) Persistence lives in the imperative shell; the functional core never touches it. The `store` functions (SKILL.md, Repository vs. ORM) are built where the ORM handle lives, the module's wiring, and handed in. An ORM-mapped class is a record, not the domain type: data returning from the store has crossed a frame (2), so rows are parsed into domain types at the persistence edge, not trusted because "we wrote them".

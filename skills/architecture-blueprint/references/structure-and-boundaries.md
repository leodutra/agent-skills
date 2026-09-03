# Structure & Boundaries

Physical organization, module APIs, dependency control. (Keyword conventions: see SKILL.md. Tags `(n)` name the deriving principle in `first-principles.md`; `(ledger)` its pattern-ledger entry.)

## Modular monolith (default)

(5, 2, 10) Default to one deployable, one codebase, with explicit internal module boundaries; modules talk by direct call or event per `events-and-consistency.md`. Modules evolve independently inside it. A module boundary inside one process is a cheap frame crossing; a service boundary is the same crossing paid over a network on every call, in an environment that can duplicate, reorder, and drop. Buy that only when operations demand it.

```text
Application
├── Orders
├── Inventory
├── Shipping
├── Billing
└── Notifications
```

Microservices come later (Evolution Path Stage 5). You MUST NOT start with microservices; extract a service ONLY when operational reality (scaling, deployment isolation, team ownership) demands it.

## Top-level structure

(13, 14; ledger: vertical slice) Within the application source tree (for example, `src/`), top-level folders MUST be **business capabilities**. The ONLY sanctioned non-capability entries there are optional `platform/` and `tests/`. Repository-level support folders such as `docs/adr/` and, in Rust repositories, `xtask/` MAY exist alongside the source tree. The folder shape is a *convention* this skill stipulates so every codebase reads the same way; the requirement it implements is grouping by shared reason for change with evidence kept local, and a business capability is the unit whose parts change together.

```text
src/
├── main                 # composition root (a file, not a folder)
├── orders/
├── inventory/
├── shipping/
├── billing/
├── notifications/
├── platform/
└── tests/
    ├── acceptance/
    ├── architecture/
    ├── e2e/
    └── performance/
```

`tests/` holds ONLY cross-module/system tests, in exactly these four canonical buckets (see `testing-and-governance.md`); single-module tests are colocated, and you MUST NOT invent other source-tree top-level test folders.

`platform/` MAY exist ONLY for cross-cutting, business-free technical substrate with no owning capability. It SHOULD appear ONLY when 2+ capabilities need it. It SHOULD NOT exist if it would be empty.

`platform/` MAY hold time/identity primitives, observability substrate, generic technical error primitives, and business-free technical utilities. It MUST NOT hold the composition root (see Composition root).

Business logic, domain types, policies, permissions, and decisions MUST NOT live in `platform/`. When in doubt, code SHOULD live in a capability. If code in `platform/` acquires business meaning, it MUST move to the owning capability. `platform/` is tolerated for one reason (13): substrate with no business reason to change. Cohabitation of things with different reasons to change is the ledger's `utils`/`common` defect, whatever the folder is called.

## Module structure

(13, 14) Organize by **vertical slices** (feature folders) as the primary unit. Domain primitives live under `domain/`; cross-slice shared decisions under `policies/`.

```text
orders/
├── api/                 # only entry point other modules may import
├── domain/              # concepts, invariants, newtypes, value objects
├── policies/            # decision logic shared by 2+ slices (optional)
├── store                # narrow persistence functions over the ORM (optional)
├── create-order/        # vertical slices — the primary unit
├── cancel-order/
├── refund-order/
├── approve-order/
└── README.md
```

Technical-layer folders (`controllers/`, `services/`, `repositories/`, `models/`) MUST NOT appear at any level (*convention*; the derived requirement is 13 — group by shared reason for change, never by technical kind). The sanctioned non-slice entries inside a module are `api/`, `domain/`, `policies/`, `store`, and `README.md`. Newtypes and value objects live in `domain/`, NOT in separate `newtypes/`/`value-objects/` folders. You MAY break out subfolders ONLY when volume makes `domain/` hard to scan. `domain/`, `policies/`, and `store` appear as they are earned; a young module MAY have only `api/` and slice folders. Logic SHOULD default to the slice that uses it, and graduate to `policies/` or onto a `domain/` object ONLY when a SKILL.md trigger fires (13 — escalate structure on evidence).

## Feature organization

(13) A mature feature is a folder; a small one MAY start as a single file and grow when it earns it. You SHOULD NOT pre-split a one-function feature.

```text
refund-order/
├── handler
├── schema
├── events
├── tests       # colocated (owns this slice)
└── README
```

## Command / query separation

(6 — exercising authority and reporting state are different acts) Conceptual distinction ONLY: **commands** change state (`createOrder()`, `refundOrder()`); **queries** read state (`getOrder()`, `searchOrders()`). Separated, questions are free and changes are accountable. This MUST NOT be read as requiring CQRS (separate models/stores); adopt CQRS ONLY with demonstrated need (ledger — the separation must be worth its edges, 5).

## Module public API

(5, 2 — a module boundary is a frame crossing, and the API is where knowledge is re-acquired) Each module MUST expose a narrow public API. Other modules MUST depend ONLY on it.

```text
orders/
└── api/
    ├── createOrder
    ├── refundOrder
    └── getOrder
```

Allowed: import `orders/api`. Forbidden: import `orders/domain`, `orders/policies`, `orders/store`, or any internal path. Other modules MUST NOT do this.

**The observable surface is the real interface** (5). Whatever another module can notice and that repeats becomes a de facto contract, promised or not: its tables, its event payload internals, its timing. A module MUST NOT read or write another module's tables; persistence sits inside the boundary. Internal paths MUST be unreachable in practice — enforced by fitness functions once boundaries matter — because a convention is a request and structure is a constraint (3). An interface states capability, not machinery: what `api/` exposes SHOULD be the complete list of what may be relied upon (14).

## Module README

(14 — what is needed to verify a thing should live near the thing) Each module MUST carry a `README.md` covering (*convention* on the list): purpose, public API, domain concepts (ubiquitous language), published events, consumed events, dependencies (and why), consistency model. It is a second copy of what the code holds, so it is kept short and MUST be kept current. It is testimony (3): it informs the reader and enforces nothing; enforcement is the fitness functions' job.

## Dependency direction

(5, 14 — contracts must compose) Dependencies MUST be explicit, one-way, and acyclic.

```text
Orders → Inventory
Orders → Billing
Shipping ✕ Orders        (forbidden)
```

Document direction (READMEs + ADR). Once boundaries matter, you MUST enforce it with architecture fitness functions (see `testing-and-governance.md`). Documentation alone CANNOT enforce boundaries (3).

## Anti-corruption boundary

(2, 8, 13; ledger: anti-corruption layer) An external model MUST NOT reach the domain in its own vocabulary. Every integration crosses a translation step — one translation per crossing (8), so the foreign vocabulary never becomes ambient and its change-sensitivity stays contained at one point (13):

```text
Stripe / Shopify / Salesforce / ERP / legacy model
        ↓  gateway  (the boundary)
        ↓  translator  (their words → ours)
internal Payment / Customer / Order
```

The `gateway` owns the call; the `translator` owns the vocabulary. Their field names, enums, error shapes, and nulls MUST stop at that line — once translated, the system speaks ONE language inward. A foreign type appearing in `domain/` or in a slice signature is a defect, and it is how a vendor's model quietly becomes your model.

## Composition over inheritance

(5, 14; ledger) You MUST NOT build business behavior through inheritance hierarchies (`BaseService → AbstractService → ConcreteService`). Compose instead: small types, plain functions, traits/interfaces satisfied by delegation, generic parameters, enums for closed variation, newtypes for distinction. Assembled parts couple by narrow contract; inheritance couples implicitly to the whole base behavior (5). Extending a base class a framework requires is a technique, not a design.

Shared behavior SHOULD be a function the callers call, NOT a base class the callers extend. An inheritance chain hides where behavior actually comes from and MUST be read end-to-end before any one method can be trusted — the opposite of the local checkability this blueprint optimizes for (14). In Rust this is the language model rather than a preference; in TypeScript and Python the rule holds anyway.

## Composition root

(6, 7; ledger: inversion of control / composition root) Concrete infrastructure MUST be assembled in ONE place — the composition root: `main` at the source root (the binary's `main.rs`, `main.ts`, `__main__.py`). Acquisition and orchestration authority is relocated to one designated assembler; components receive, and the wiring has one home. The root MUST NOT live in `platform/`: the root imports every capability, and every capability imports `platform/`, so a root inside it is a dependency cycle (5, 14).

```text
main
 ↓  config (already parsed into typed values)
 ↓  database pool, clients, bus
 ↓  module wiring (each module's store functions and handlers built over the pool)
 ↓  HTTP server / workers
```

Business code MUST receive its dependencies and MUST NOT construct infrastructure itself: no connection opened inside a use case, no HTTP client instantiated in a policy, no global singleton reached for. The composition root is then the only file that knows every concrete choice, and the functional core stays reachable in tests without infrastructure.

A composition root is NOT a DI container. You SHOULD wire by hand with plain constructor arguments; adopt a container ONLY when hand-wiring is demonstrably unmanageable.

**No ambient authority** (7; ledger-rejected: service locator, ambient singleton / global state). No service locator, no global registry, no module-level mutable singleton, no `getInstance()`: each is a hidden input to everything and a hidden output of everything — the densest possible edge (5, 6). A singleton the root constructs once and hands in explicitly is not ambient; the defect is discovery, not uniqueness.

## Capability-oriented dependencies

(5, 6, 7; ledger: capability interface, dependency injection) Pass the narrowest capability that does the job. A slice needing to load one user MUST NOT receive the whole database handle, ORM, or a god `Service` object.

```text
❌ handler(db: Database)
✅ handler(loadUser: LoadUser, publishEvent: PublishEvent)
```

What a slice cannot reach, it cannot misuse (6 — authority proportional to responsibility), every reader of the slice can see its true domain (7), and its tests supply only what it names (5 — depend on the least that suffices). Passing one `Context`/`AppState` object carrying everything into every slice is the god context (ledger-rejected): every reader must account for what every holder could do. The narrow functions themselves are built where the handle lives — the module's `store` for persistence, a `gateway` for an external system — and handed to the slice by the module wiring.

**The capability is the seam** (13, 7, 5; ledger: ports and adapters). A dependency on the world — persistence, network, clock, randomness, queue — earns its seam by being the world: the test double that stands in for it is the second implementation the ledger asks for, and often the only one a codebase ever needs. Shape follows need: one operation is a function type (in Rust, a one-method trait behind a generic parameter is that function type's idiomatic form); a bundle of operations that travel together is a trait/interface. You MUST NOT put an interface over pure, in-process code with no world behind it: that is interface-for-everything (13, 5; ledger-rejected), insurance bought against imaginable change and paid in certain edges. This is the capability thinking of `authorization.md` — least authority, granted explicitly — applied to code dependencies.

## State ownership

(6, 12; ledger: ownership / single writer) For every piece of mutable state, ONE owner MUST be nameable:

```text
application  → configuration
module       → its store / connection pool
task         → its local state
actor        → the state behind its mailbox
request      → request-scoped data
```

Shared mutable state with no named owner is a defect. Ask who owns the fact before adding a lock; naming the owner often deletes the synchronization rather than fixing it. Where several writers are unavoidable, the explicit resolution rule — an ordering, a lawful merge, a designated arbiter — is the owner (6); writers with no such rule are a negotiation with no chair. Immutable by default (6): mutability is a grant of authority and SHOULD be as deliberate as any other grant.

**Lifetime is a fact like any other** (12; ledger: RAII / scoped guards, structured concurrency). `Lifetime(resource) ⊆ Lifetime(owner)`: possession of a handle SHOULD prove the resource is live, and release SHOULD be a structural consequence of the owner's end, not a remembered duty. Where the language expresses scope-bound resources (Rust ownership and `Drop`, Python context managers, `defer`/`using`), you SHOULD let scope release the resource instead of releasing it by hand, and SHOULD hold a lock for the shortest scope that is still correct. **Initiated work is owned work:** a task spawned by a request or component MUST be enclosed in its initiator's lifetime so cancellation and teardown reach it; a detached task is a resource with no owner, alive by accident. Endings deserve the care of beginnings: teardown SHOULD release in reverse order of acquisition, so no enclosure is broken before what it encloses is gone.

## Strategic DDD only

(frame; 5 — indirection is an edge, not a virtue) Use bounded contexts, ubiquitous language, domain ownership, explicit business concepts. You MUST NOT import the tactical-DDD pattern zoo (aggregates/repositories/factories/specifications everywhere) by default; pull a pattern in ONLY when a specific problem calls for it — the ledger names the condition each one binds under.

## Role vocabulary (file and folder names)

This vocabulary names the **role a file plays**, which is a different axis from SKILL.md's Naming rules (those govern functions, types, and events, which MUST speak the business language). `handler.ts` is a legitimate file name; `handle()` as a business operation is not. Both apply at once: `refund-order/handler.ts` exporting `refundOrder()`.

Rules for using it:

- Name by **responsibility**, not by technical kind. A file MUST NOT carry a role name it does not actually fulfil (`repository.ts` that wraps one ORM call is a mislabel — that is a `store`).
- This is a **catalog to pull from, not a folder tree to create**. Most slices need three or four of these names, ever. Creating the full set is the pattern-zoo failure this blueprint forbids.
- **Singular for a file, plural for a folder** of several: `validator.ts`, `policies/`.
- **One role per file.** A file needing two role names SHOULD be split — or the names are wrong.
- These names live *inside* a module. Top-level source folders MUST still be business capabilities.
- In snake_case languages, transliterate: `use_case.py`, `value_object.rs`, `refund_policy.py`.
- Each role name is a pattern-level word (§The ladder of statements in `first-principles.md`): it binds only where the obligation it discharges exists. The note under each category names the deriving principle.

### Input, output, and shape

(8 — one translation per crossing, normalize once at the edge; 2 — structural reconstruction is not semantic proof)

| Role | Responsibility | Where it lives / caveat |
| --- | --- | --- |
| `parser` | Raw representation → structure | Slice boundary. SHOULD produce domain types directly (parse, don't validate) |
| `schema` | Declares the contract/shape of data at a boundary | Slice |
| `serializer` | Structure → serialized representation | Slice |
| `deserializer` | Serialized representation → structure | Slice. `codec` MAY name the pair when they are symmetric and co-located |
| `formatter` | Structure → presentation form for humans | Slice; `platform/` only if business-free |
| `mapper` | Model A → model B across one boundary | Slice |
| `converter` | Value/type conversion between representations | `domain/` if the types are domain types, else `platform/` |
| `normalizer` | Puts data in canonical form | Slice or `domain/` |
| `sanitizer` | Removes or neutralizes unwanted/unsafe input | Trust boundary. MUST NOT be skipped as "simplification" |
| `presenter` / `view-model` | Shapes data for one specific view | Read-side slice |
| `contract` | Shape published to external consumers | `api/`. Changing it is a breaking change |
| `translator` | Maps a foreign model into our language (anti-corruption) | Next to the `gateway` it protects |

### Validation

(1 — establish by transformation, not by inspection)

| Role | Responsibility | Where it lives / caveat |
| --- | --- | --- |
| `validator` | Verifies data validity at a boundary | Subordinate to `parser`, never a peer: it MUST yield typed domain values, NOT a boolean or error list that leaves the raw shape in play downstream. A `validator` called below the boundary is a defect (see Parse, don't validate in `domain-modeling.md`) |
| `matcher` | Tests a value against a criterion | Slice |
| `specification` | Composable predicate (`isSatisfiedBy`) | Rare. ONLY when composing predicates or driving queries (see `domain-modeling.md`) |

### Application (the slice)

(14, 11 — one business operation's orchestration in one place, often the natural consistency scope; ledger: use case)

| Role | Responsibility | Where it lives / caveat |
| --- | --- | --- |
| `handler` | Entry point of one operation; orchestrates | Slice. The default slice entry point |
| `use-case` | One business operation | Synonym of `handler`. You SHOULD pick ONE of the two per codebase and keep it consistent (*convention*) |
| `command` | Intent to change state | Slice. Conceptual only — MUST NOT be read as requiring CQRS |
| `query` | A read operation | Slice |
| `resolver` | Resolves a value, resource, or implementation on demand | Slice |
| `middleware` | Cross-cutting step in a request pipeline; each step adds a property the next can rely on | `platform/`. MUST stay business-free (ledger: middleware pipeline) |
| `saga` / `process-manager` | Coordinates a multi-step workflow across consistency scopes, with compensation | Module level, Stage 3+. ONLY when a real workflow spans scopes and can fail midway; it exists to model the intermediate states (11) |
| `job` / `task` | Unit of scheduled or deferred work | Slice. MUST be idempotent (10) and owned by a lifetime (12) |

### Domain

(1, 3, 4 — receipts, distinctions in the medium, representable matched to meaningful)

| Role | Responsibility | Where it lives / caveat |
| --- | --- | --- |
| newtype | Distinguishes same-typed primitives (ids) | `domain/`. On from Stage 1 |
| `value-object` | Concept defined by its value; immutable, self-validating | `domain/` |
| `entity` | Identity, lifecycle, and invariants | `domain/`. Rich behavior ONLY on a SKILL.md trigger |
| `policy` | A business decision or rule | Slice by default; `policies/` when shared by 2+ slices |
| `process` / `reaction` | Reactive when-then logic | Slice. MUST NOT be called a policy |
| `factory` | Non-trivial construction | `domain/`. ONLY when construction itself carries rules |
| `builder` | Incremental construction of a complex value | Rare. ONLY for genuinely many optional parts |
| `domain-service` | Domain behavior belonging to no single entity or value object | `domain/`. Prefer a pure function in the functional core first |
| `events` | Past-tense business facts | Slice (`events`) or `domain/` |
| `errors` | Typed domain failures | `domain/`. Technical error primitives MAY live in `platform/` |

### Persistence

(6 — localized persistence authority; 11 — the consistency scope; 2 — trust follows custody)

| Role | Responsibility | Where it lives / caveat |
| --- | --- | --- |
| `store` | Narrow persistence functions over the ORM/query builder (`loadOrder`, `saveOrder`) that slices receive as capabilities | Module level. The Stage-1 default: a direct ORM call behind a function boundary, no repository object. Parses rows into domain types (2) |
| `repository` | Aggregate-shaped load/save that models a domain persistence boundary | NOT the default. ONLY with rules of its own, cross-slice query reuse, or a real planned storage swap; a `store` otherwise; never one per table (ledger) |
| `read-model` | Shape optimized for one read path | Read-side slice. A copy of facts (6): named home, stated staleness |
| `projection` | Builds/updates a read model from events | Slice. Only where events already exist; MUST be idempotent (10) |
| `unit-of-work` / `transaction` | The consistency scope made mechanical: jointly-necessary facts move in one act | Imperative shell or `platform/`. Drawn no larger than its invariants demand (11) |
| `cache` | Cache abstraction | `platform/`. A second copy of a fact (6): ONLY with a named authoritative home, a staleness bound, and a measured need |
| `migration` | Schema/data migration | Module `migrations/` or repository level |
| `outbox` | Records pending publishes in the same scope as the state change | ONLY when a state change and a publish must both happen across separate scopes and at-least-once delivery is actually required (11, 10) |

### Integration

(2 — every crossing is a re-acquisition of knowledge; 13 — the mechanism's change-sensitivity contained at one translation point)

| Role | Responsibility | Where it lives / caveat |
| --- | --- | --- |
| `gateway` | Boundary to an external system, expressed in our language | Module or slice |
| `client` | Concrete transport/protocol implementation | Behind the gateway, or `platform/` |
| `adapter` | Adapts one interface to another | ONLY where two real, existing interfaces meet (ledger) |
| `port` | Interface the module owns for an outbound need | ONLY over a world dependency (persistence, network, queue, clock); shape follows need — one operation is a function type, a bundle is a trait (see Capability-oriented dependencies) |

### Messaging

(1 — execution leaves receipts; 10 — semantics invariant under duplication and reordering; 11)

`event` = a domain fact that happened. `message` = the transport envelope carrying it. You MUST NOT use the words interchangeably (*convention*, motivated by 3).

| Role | Responsibility | Where it lives / caveat |
| --- | --- | --- |
| `event` | Past-tense business fact | `domain/` or slice. Naming rules in `events-and-consistency.md` |
| `event-publisher` | Publishes domain events | Slice or module |
| `event-handler` / `subscriber` | Reacts to an event | Consuming slice. MUST be idempotent (10) |
| `message-publisher` / `message-consumer` | Transport-level send/receive | `platform/`. Business-free |

### Security

(7 — identity and permission are inputs; 6 — decisions live with the authority; 2 — evidence travels, acceptance cannot)

| Role | Responsibility | Where it lives / caveat |
| --- | --- | --- |
| `authentication` | Establishes who the actor is | Edge / `platform/` |
| `authorization` | `can*` policy: may this actor do this | `policies/` or beside the slice; checked at use-case entry, deny-by-default |
| `guard` | Enforcement point that *invokes* an authorization policy | Edge. MUST NOT contain the decision itself or any role conditional |

### Platform substrate

(7 — time, chance, identity, and configuration are inputs, so they are handed in from here rather than discovered) Business-free technical concerns: `config`, `logger`, `telemetry`, `clock` / `time-provider`, `id-generator`, `feature-flags`. These live in `platform/`, and ONLY once 2+ capabilities need them. Any of these that acquires business meaning MUST move to the owning capability.

### Computation

(8 — separate calculation from interaction; the functional core)

| Role | Responsibility | Where it lives / caveat |
| --- | --- | --- |
| `calculator` | Encapsulated calculation | Functional core of the slice, or `policies/` when shared |
| `extractor` | Pulls information out of a larger structure | Slice |
| `selector` | Selects/derives a subset of data | Slice |

### Tests

Colocated with the slice they cover (see `testing-and-governance.md`). Supporting names: `fixtures` (static data), `builders` (test data construction), `fakes` (in-memory doubles). Cross-module tests only in the four canonical `tests/` buckets.

### `utils` and `helpers`

Both are legitimate names. Both are also a signal that the code has **no more specific architectural responsibility**. Preference ladder:

```text
specific role name  →  utils  →  helpers
```

```text
❌ utils/validate.ts       ✅ parser.ts / schema.ts
❌ utils/parse.ts          ✅ parser.ts
❌ utils/transform.ts      ✅ mapper.ts
❌ helpers/save.ts         ✅ store.ts (narrow functions over the ORM)
❌ helpers/checkAccess.ts  ✅ policies/canRefundOrder.ts
```

The ledger rejects `utils`/`common` modules for cohabitation without a shared reason for change (13) — a module named for having no name. `utils` is tolerated for exactly the code that passes that test: small, generic, business-free, dependency-free functions with no reason to change at all — stdlib-shaped code with no owning capability. Those belong in `platform/`, not at a module's top level, and the first entry with a business or infrastructure reason to change MUST move out:

```text
platform/utils/
├── clamp
├── sleep
├── isDefined
└── groupBy
```

`helpers` is reserved for **local, contextual** plumbing of one slice — reshaping that carries no rule — and MUST stay inside that slice:

```text
create-order/
├── handler
└── helpers/
    ├── group-lines-by-sku
    └── zip-lines-with-prices
```

A `utils` or `helpers` folder that accumulates business rules or calculations is a defect; the rules MUST move to a policy, a domain type, or the slice's functional core (`calculator`).

### Names to avoid

(13 — cohabitation without a shared reason for change; 3 — renaming without removing) You SHOULD NOT use: `manager`, bare `service` (`OrderService` doing everything), `common`, `shared`, `core`, `base`, `impl`, `misc`, `data`, `models`, `dto`. Each names a technical bucket rather than a responsibility, and each grows without limit because nothing is out of scope for it. Layer folders (`controllers/`, `services/`, `repositories/`) are forbidden under Module structure. A wrapper that only forwards to another wrapper (`Service → Manager → Repository → ORM`) is wrapper-on-wrapper ceremony (ledger-rejected): each layer an edge that deletes nothing.

### In a real vertical slice

Roles appear where they are earned, never as a uniform template:

```text
features/orders/
├── create/
│   ├── handler
│   ├── schema
│   ├── mapper
│   └── serializer
├── cancel/
│   ├── handler
│   └── policy
└── get/
    ├── handler
    ├── query
    └── serializer
```

Three slices, three different shapes. A slice whose folder mirrors its siblings role-for-role is usually a template that was copied rather than a design that was chosen.

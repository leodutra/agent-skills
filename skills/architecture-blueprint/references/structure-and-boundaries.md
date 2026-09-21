# Structure & Boundaries

Physical organization, module APIs, dependency control, ownership. File and folder role names (`handler`, `store`, `gateway`…) are in `role-vocabulary.md`. (Keywords and the `(n)` / `(frame)` / `(ledger)` tags: see SKILL.md.)

## Modular monolith (default)

(5, 2, 10) Default to one deployable, one codebase, with explicit internal module boundaries; modules evolve independently inside it and talk by direct call or event per `events-and-consistency.md`. A module boundary inside one process is a cheap frame crossing; a service boundary is the same crossing paid over a network on every call, in an environment that can duplicate, reorder, and drop. You MUST NOT start with microservices; extract a service ONLY when operational reality (scaling, deployment isolation, team ownership) demands it (Evolution Path Stage 5).

## Strategic DDD only

(frame; 5 — indirection is an edge, not a virtue) Use bounded contexts, ubiquitous language, domain ownership, explicit business concepts. You MUST NOT import the tactical-DDD pattern zoo (aggregates/repositories/factories/specifications everywhere) by default; pull a pattern in ONLY when a specific problem calls for it — the ledger names the condition each one binds under.

## Top-level structure

(13, 14; ledger: vertical slice) Within the application source tree (for example, `src/`), top-level folders MUST be **business capabilities**. The ONLY sanctioned non-capability entries there are optional `platform/` and `tests/`; any other technical-concern folder there is a defect. Repository-level support folders such as `specs/` (specifications and ADRs, `specs/adr/`) and, in Rust repositories, `xtask/` MAY exist alongside the source tree. The folder shape is a *convention* this skill stipulates so every codebase reads the same way; the requirement it implements is grouping by shared reason for change with evidence kept local, and a business capability is the unit whose parts change together.

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

**`tests/`** holds ONLY cross-module/system tests, in exactly these four canonical buckets; single-module tests are colocated, and you MUST NOT invent other source-tree top-level test folders (see `testing-and-governance.md`).

**`platform/`** MAY exist ONLY for cross-cutting, business-free technical substrate with no owning capability: time/identity primitives, observability substrate, generic technical error primitives, business-free technical utilities. It SHOULD appear ONLY when 2+ capabilities need it, and SHOULD NOT exist if it would be empty. It MUST NOT hold the composition root (see Composition root), and MUST NOT hold business logic, domain types, policies, permissions, or decisions. When in doubt, code SHOULD live in a capability; code in `platform/` that acquires business meaning MUST move to the owning capability. `platform/` is tolerated for one reason (13): substrate with no business reason to change. Cohabitation of things with different reasons to change is the ledger's `utils`/`common` defect, whatever the folder is called.

## Module structure

(13, 14) Organize by **vertical slices** (feature folders) as the primary unit. Domain primitives live under `domain/`; cross-slice shared decisions under `policies/`.

```text
orders/
├── api/                 # only entry point other modules may import
├── create-order/        # vertical slices — the primary unit
├── cancel-order/
├── refund-order/
├── approve-order/
├── domain/              # shared vocabulary: newtypes, value objects, invariants — not a layer
├── policies/            # decision logic shared by 2+ slices (optional)
├── store                # narrow persistence functions over the ORM (optional)
└── README.md
```

- Technical-layer folders (`controllers/`, `services/`, `repositories/`, `models/`) MUST NOT appear at any level (*convention*; the derived requirement is 13 — group by shared reason for change, never by technical kind).
- The sanctioned non-slice entries inside a module are `api/`, `domain/`, `policies/`, `store`, and `README.md`. `domain/`, `policies/`, and `store` appear as they are earned; a young module MAY have only `api/`, its `README.md`, and slice folders.
- Newtypes and value objects live in `domain/`, NOT in separate `newtypes/`/`value-objects/` folders. You MAY break out subfolders ONLY when volume makes `domain/` hard to scan.
- Logic SHOULD default to the slice that uses it, and graduate to `policies/` or onto a `domain/` object ONLY when a SKILL.md trigger fires (13 — escalate structure on evidence).

## Feature organization

(13) A mature feature is a folder; a small one MAY start as a single file holding everything below, and splits when it earns it. You SHOULD NOT pre-split a one-function feature.

```text
refund-order/
├── handler
├── command           # the action type
├── authorization     # impl Can for the action (see authorization.md)
├── schema
├── events
├── tests             # colocated (owns this slice)
└── README
```

Roles appear where they are earned, never as a uniform template (see `role-vocabulary.md`).

## Command / query separation

(6 — exercising authority and reporting state are different acts) Conceptual distinction ONLY: **commands** change state (`createOrder()`, `refundOrder()`); **queries** read state (`getOrder()`, `searchOrders()`). Separated, questions are free and changes are accountable. This MUST NOT be read as requiring CQRS (separate models/stores); adopt CQRS ONLY with demonstrated need (ledger — the separation must be worth its edges, 5).

## Module public API

(5, 2 — a module boundary is a frame crossing, and the API is where knowledge is re-acquired) Each module MUST expose a narrow public API (`orders/api/`: `createOrder`, `refundOrder`, `getOrder`), and other modules MUST depend ONLY on it. Other modules MUST NOT import `orders/domain`, `orders/policies`, `orders/store`, or any other internal path.

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

Document direction (READMEs + ADR). Once boundaries matter, you MUST enforce it with architecture fitness functions (see `testing-and-governance.md`); documentation alone CANNOT enforce boundaries (3).

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

(5, 14; ledger) You MUST NOT build business behavior through inheritance hierarchies (`BaseService → AbstractService → ConcreteService`). Compose instead: small types, plain functions, traits/interfaces satisfied by delegation, generic parameters, enums for closed variation, newtypes for distinction. Shared behavior SHOULD be a function the callers call, NOT a base class the callers extend. Assembled parts couple by narrow contract; inheritance couples implicitly to the whole base behavior (5), hides where behavior actually comes from, and MUST be read end-to-end before any one method can be trusted — the opposite of local checkability (14). Extending a base class a framework requires is a technique, not a design. In Rust this is the language model rather than a preference; in TypeScript and Python the rule holds anyway.

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

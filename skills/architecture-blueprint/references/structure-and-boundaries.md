# Structure & Boundaries

Physical organization, module APIs, dependency control. (Keyword conventions: see SKILL.md.)

## Modular monolith (default)

Default to one deployable, one codebase, with explicit internal module boundaries and internal event communication. Modules evolve independently inside it.

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

Within the application source tree (for example, `src/`), top-level folders MUST be **business capabilities**. The ONLY sanctioned non-capability entries there are optional `platform/` and `tests/`. Repository-level support folders such as `docs/adr/` and, in Rust repositories, `xtask/` MAY exist alongside the source tree.

```text
src/
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

`platform/` MAY exist ONLY for cross-cutting, business-free technical substrate with no owning capability. It SHOULD appear ONLY when 2+ capabilities need it. It SHOULD NOT exist if it would be empty or mostly generic helpers.

`platform/` MAY hold time/identity primitives, observability substrate, generic technical error primitives, business-free technical utilities, and app-wide bootstrap wiring with no owning capability.

Business logic, domain types, policies, permissions, and decisions MUST NOT live in `platform/`. When in doubt, code SHOULD live in a capability. If code in `platform/` acquires business meaning, it MUST move to the owning capability.

## Module structure

Organize by **vertical slices** (feature folders) as the primary unit. Domain primitives live under `domain/`; cross-slice shared decisions under `policies/`.

```text
orders/
├── api/                 # only entry point other modules may import
├── domain/              # concepts, invariants, newtypes, value objects
├── policies/            # decision logic shared by 2+ slices (optional)
├── create-order/        # vertical slices — the primary unit
├── cancel-order/
├── refund-order/
├── approve-order/
└── README.md
```

Newtypes and value objects MUST live in `domain/`, NOT in separate `newtypes/`/`value-objects/` folders (that organizes by technical kind — the layering this blueprint forbids). You MAY break out subfolders ONLY when volume makes `domain/` hard to scan. `domain/` and `policies/` appear as stages are reached; a young module MAY have only `api/` and slice folders. Logic SHOULD default to the slice that uses it, and graduate to `policies/` or onto a `domain/` object ONLY when a SKILL.md trigger fires.

## Feature organization

A mature feature is a folder; a small one MAY start as a single file and grow when it earns it. You SHOULD NOT pre-split a one-function feature.

```text
refund-order/
├── handler
├── schema
├── events
├── tests       # colocated (owns this slice)
└── README
```

## Command / query separation

Conceptual distinction ONLY: **commands** change state (`createOrder()`, `refundOrder()`); **queries** read state (`getOrder()`, `searchOrders()`). This MUST NOT be read as requiring CQRS (separate models/stores); adopt CQRS ONLY with demonstrated need.

## Module public API

Each module MUST expose a narrow public API. Other modules MUST depend ONLY on it.

```text
orders/
└── api/
    ├── createOrder
    ├── refundOrder
    └── getOrder
```

Allowed: import `orders/api`. Forbidden: import `orders/domain`, `orders/policies`, or any internal path. Other modules MUST NOT do this.

## Module README

Each module MUST carry a `README.md` covering: purpose, public API, domain concepts (ubiquitous language), published events, consumed events, dependencies (and why), consistency model. It MUST be kept current.

## Dependency direction

Dependencies MUST be explicit, one-way, and acyclic.

```text
Orders → Inventory
Orders → Billing
Shipping ✕ Orders        (forbidden)
```

Document direction (READMEs + ADR). Once boundaries matter, you MUST enforce it with architecture fitness functions (see `testing-and-governance.md`). Documentation alone CANNOT enforce boundaries.

## Anti-corruption boundary

An external model MUST NOT reach the domain in its own vocabulary. Every integration crosses a translation step:

```text
Stripe / Shopify / Salesforce / ERP / legacy model
        ↓  gateway  (the boundary)
        ↓  translator  (their words → ours)
internal Payment / Customer / Order
```

The `gateway` owns the call; the `translator` owns the vocabulary. Their field names, enums, error shapes, and nulls MUST stop at that line — once translated, the system speaks ONE language inward. A foreign type appearing in `domain/` or in a slice signature is a defect, and it is how a vendor's model quietly becomes your model.

## Composition over inheritance

You MUST NOT build behavior through inheritance hierarchies (`BaseService → AbstractService → ConcreteService`). Compose instead: small types, plain functions, traits/interfaces satisfied by delegation, generic parameters, enums for closed variation, newtypes for distinction.

Shared behavior SHOULD be a function the callers call, NOT a base class the callers extend. An inheritance chain hides where behavior actually comes from and MUST be read end-to-end before any one method can be trusted — the opposite of the locality this blueprint optimizes for. In Rust this is the language model rather than a preference; in TypeScript and Python the rule holds anyway.

## Composition root

Concrete infrastructure MUST be assembled in ONE place — the composition root (`main`, or app-wide bootstrap in `platform/`).

```text
main
 ↓  config (already parsed into typed values)
 ↓  database pool, clients, bus
 ↓  module wiring
 ↓  HTTP server / workers
```

Business code MUST receive its dependencies and MUST NOT construct infrastructure itself: no connection opened inside a use case, no HTTP client instantiated in a policy, no global singleton reached for. The composition root is then the only file that knows every concrete choice, and the functional core stays reachable in tests without infrastructure.

A composition root is NOT a DI container. You SHOULD wire by hand with plain constructor arguments; adopt a container ONLY when hand-wiring is demonstrably unmanageable.

## Capability-oriented dependencies

Pass the narrowest capability that does the job. A slice needing to load one user MUST NOT receive the whole database handle, ORM, or a god `Service` object.

```text
❌ handler(db: Database)
✅ handler(loadUser: LoadUser, publishEvent: PublishEvent)
```

What a slice cannot reach, it cannot misuse, and its tests supply only what it names. Express the capability as a function parameter first; promote it to a trait/interface ONLY under the `port` rule (2+ real implementations or a committed swap). This is the capability thinking of `authorization.md` — least authority, granted explicitly — applied to code dependencies.

## State ownership

For every piece of mutable state, ONE owner MUST be nameable:

```text
application  → configuration
module       → its store / connection pool
task         → its local state
actor        → the state behind its mailbox
request      → request-scoped data
```

Shared mutable state with no named owner is a defect. Most synchronization bugs are ownership questions that were never answered, and naming the owner usually deletes the synchronization rather than fixing it.

Where the language expresses scope-bound resources (Rust ownership and `Drop`, Python context managers, `defer`/`using`), you SHOULD let scope release the resource instead of releasing it by hand, and SHOULD hold a lock for the shortest scope that is still correct.

## Strategic DDD only

Use bounded contexts, ubiquitous language, domain ownership, explicit business concepts. You MUST NOT import the tactical-DDD pattern zoo (aggregates/repositories/factories/specifications everywhere) by default; pull a pattern in ONLY when a specific problem calls for it.

## Role vocabulary (file and folder names)

This vocabulary names the **role a file plays**, which is a different axis from SKILL.md's Naming rules (those govern functions, types, and events, which MUST speak the business language). `handler.ts` is a legitimate file name; `handle()` as a business operation is not. Both apply at once: `refund-order/handler.ts` exporting `refundOrder()`.

Rules for using it:

- Name by **responsibility**, not by technical kind. A file MUST NOT carry a role name it does not actually fulfil (`repository.ts` that wraps one ORM call is a mislabel).
- This is a **catalog to pull from, not a folder tree to create**. Most slices need three or four of these names, ever. Creating the full set is the pattern-zoo failure this blueprint forbids.
- **Singular for a file, plural for a folder** of several: `validator.ts`, `policies/`.
- **One role per file.** A file needing two role names SHOULD be split — or the names are wrong.
- These names live *inside* a module. Top-level source folders MUST still be business capabilities.
- In snake_case languages, transliterate: `use_case.py`, `value_object.rs`, `refund_policy.py`.

### Input, output, and shape

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

| Role | Responsibility | Where it lives / caveat |
| --- | --- | --- |
| `validator` | Verifies data validity at a boundary | Subordinate to `parser`, never a peer: it MUST yield typed domain values, NOT a boolean or error list that leaves the raw shape in play downstream. A `validator` called below the boundary is a defect (see parse-don't-validate) |
| `matcher` | Tests a value against a criterion | Slice |
| `specification` | Composable predicate (`isSatisfiedBy`) | Rare. ONLY when composing predicates or driving queries (see `domain-modeling.md`) |

### Application (the slice)

| Role | Responsibility | Where it lives / caveat |
| --- | --- | --- |
| `handler` | Entry point of one operation; orchestrates | Slice. The default slice entry point |
| `use-case` | One business operation | Synonym of `handler`. Pick ONE of the two per codebase and keep it consistent |
| `command` | Intent to change state | Slice. Conceptual only — MUST NOT be read as requiring CQRS |
| `query` | A read operation | Slice |
| `resolver` | Resolves a value, resource, or implementation on demand | Slice |
| `middleware` | Cross-cutting step in a request pipeline | `platform/`. MUST stay business-free |
| `saga` / `process-manager` | Coordinates a multi-step, multi-module workflow with compensation | Module level, Stage 3+. ONLY when a real workflow spans modules and can fail midway |
| `job` / `task` | Unit of scheduled or deferred work | Slice. MUST be idempotent |

### Domain

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

| Role | Responsibility | Where it lives / caveat |
| --- | --- | --- |
| `repository` | Persists/retrieves aggregates or entities | NOT the default. ONLY for measurable value; direct ORM calls otherwise |
| `read-model` | Shape optimized for one read path | Read-side slice |
| `projection` | Builds/updates a read model from events | Slice. Only where events already exist |
| `unit-of-work` / `transaction` | Transactional boundary control | Imperative shell or `platform/` |
| `cache` | Cache abstraction | `platform/`. Add ONLY with a measured need |
| `migration` | Schema/data migration | Module `migrations/` or repository level |
| `outbox` | Records events transactionally for reliable publish | ONLY when at-least-once delivery is actually required |

### Integration

| Role | Responsibility | Where it lives / caveat |
| --- | --- | --- |
| `gateway` | Boundary to an external system, expressed in our language | Module or slice |
| `client` | Concrete transport/protocol implementation | Behind the gateway, or `platform/` |
| `adapter` | Adapts one interface to another | ONLY where two real, existing interfaces meet |
| `port` | Interface the module owns for an outbound need | ONLY with 2+ real implementations or a committed swap. MUST NOT be introduced for testability alone |

### Messaging

`event` = a domain fact that happened. `message` = the transport envelope carrying it. You MUST NOT use the words interchangeably.

| Role | Responsibility | Where it lives / caveat |
| --- | --- | --- |
| `event` | Past-tense business fact | `domain/` or slice. Naming rules in `events-and-consistency.md` |
| `event-publisher` | Publishes domain events | Slice or module |
| `event-handler` / `subscriber` | Reacts to an event | Consuming slice. MUST be idempotent |
| `message-publisher` / `message-consumer` | Transport-level send/receive | `platform/`. Business-free |

### Security

| Role | Responsibility | Where it lives / caveat |
| --- | --- | --- |
| `authentication` | Establishes who the actor is | Edge / `platform/` |
| `authorization` | `can*` policy: may this actor do this | `policies/`, checked at use-case entry, deny-by-default |
| `guard` | Enforcement point that *invokes* an authorization policy | Edge. MUST NOT contain the decision itself or any role conditional |

### Platform substrate

Business-free technical concerns: `config`, `logger`, `telemetry`, `clock` / `time-provider`, `id-generator`, `feature-flags`. These live in `platform/`, and ONLY once 2+ capabilities need them. Any of these that acquires business meaning MUST move to the owning capability.

### Computation

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
❌ helpers/save.ts         ✅ repository.ts (or a direct ORM call)
❌ helpers/checkAccess.ts  ✅ policies/canRefundOrder.ts
```

`utils` is legitimate for small, generic, business-free functions with no owning capability — and those belong in `platform/`, not at a module's top level:

```text
platform/utils/
├── clamp
├── sleep
├── isDefined
└── groupBy
```

`helpers` is reserved for **local, contextual** helpers of one slice, and MUST stay inside that slice:

```text
create-order/
├── handler
└── helpers/
    ├── calculate-items-total
    └── build-line-items
```

A `utils` or `helpers` folder that accumulates business rules is a defect; the rules MUST move to a policy, a domain type, or the slice's functional core.

### Names to avoid

You SHOULD NOT use: `manager`, bare `service` (`OrderService` doing everything), `common`, `shared`, `core`, `base`, `impl`, `misc`, `data`, `models`, `dto`. Each names a technical bucket rather than a responsibility, and each grows without limit because nothing is out of scope for it. Layer folders (`controllers/`, `services/`, `repositories/`) are already forbidden above.

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

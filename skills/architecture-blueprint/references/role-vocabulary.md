# Role Vocabulary (file and folder names)

The names a file or folder may carry, by the **role it plays**. (Keywords and the `(n)` / `(ledger)` tags: see SKILL.md.)

This is a different axis from SKILL.md's Naming rules, which govern functions, types, and events and MUST speak the business language. `handler.ts` is a legitimate file name; `handle()` as a business operation is not. Both apply at once: `refund-order/handler.ts` exporting `refundOrder()`.

## Rules

- Name by **responsibility**, not by technical kind. A file MUST NOT carry a role name it does not actually fulfil (`repository.ts` that wraps one ORM call is a mislabel — that is a `store`).
- This is a **catalog to pull from, not a folder tree to create**. Most slices need three or four of these names, ever. Creating the full set is the pattern-zoo failure this blueprint forbids.
- **Singular for a file, plural for a folder** of several: `validator.ts`, `policies/`.
- **One role per file.** A file needing two role names SHOULD be split — or the names are wrong.
- These names live *inside* a module. Top-level source folders MUST still be business capabilities.
- In snake_case languages, transliterate: `use_case.py`, `value_object.rs`, `refund_policy.py`.
- Each role name is a pattern-level word (`first-principles.md`, §The ladder of statements): it binds only where the obligation it discharges exists. The note under each category names the deriving principle.

Roles appear where they are earned, never as a uniform template:

```text
orders/
├── create-order/
│   ├── handler
│   ├── schema
│   ├── mapper
│   └── serializer
├── cancel-order/
│   ├── handler
│   └── policy
└── get-order/
    ├── handler
    ├── query
    └── serializer
```

Three slices, three different shapes. A slice whose folder mirrors its siblings role-for-role is usually a template that was copied rather than a design that was chosen.

## Input, output, and shape

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

## Validation

(1 — establish by transformation, not by inspection)

| Role | Responsibility | Where it lives / caveat |
| --- | --- | --- |
| `validator` | Verifies data validity at a boundary | Subordinate to `parser`, never a peer: it MUST yield typed domain values, NOT a boolean or error list that leaves the raw shape in play downstream. A `validator` called below the boundary is a defect (see Parse, don't validate in `domain-modeling.md`) |
| `matcher` | Tests a value against a criterion | Slice |
| `specification` | Composable predicate (`isSatisfiedBy`) | Rare. ONLY when composing predicates or driving queries (see `domain-modeling.md`) |

## Application (the slice)

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

## Domain

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

## Persistence

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

## Integration

(2 — every crossing is a re-acquisition of knowledge; 13 — the mechanism's change-sensitivity contained at one translation point)

| Role | Responsibility | Where it lives / caveat |
| --- | --- | --- |
| `gateway` | Boundary to an external system, expressed in our language | Module or slice |
| `client` | Concrete transport/protocol implementation | Behind the gateway, or `platform/` |
| `adapter` | Adapts one interface to another | ONLY where two real, existing interfaces meet (ledger) |
| `port` | Interface the module owns for an outbound need | ONLY over a world dependency (persistence, network, queue, clock); shape follows need — one operation is a function type, a bundle is a trait (see Capability-oriented dependencies in `structure-and-boundaries.md`) |

## Messaging

(1 — execution leaves receipts; 10 — semantics invariant under duplication and reordering; 11)

`event` = a domain fact that happened. `message` = the transport envelope carrying it. You MUST NOT use the words interchangeably (*convention*, motivated by 3).

| Role | Responsibility | Where it lives / caveat |
| --- | --- | --- |
| `event` | Past-tense business fact | `domain/` or slice. Naming rules in `events-and-consistency.md` |
| `event-publisher` | Publishes domain events | Slice or module |
| `event-handler` / `subscriber` | Reacts to an event | Consuming slice. MUST be idempotent (10) |
| `message-publisher` / `message-consumer` | Transport-level send/receive | `platform/`. Business-free |

## Security

(7 — identity and permission are inputs; 6 — decisions live with the authority; 2 — evidence travels, acceptance cannot)

| Role | Responsibility | Where it lives / caveat |
| --- | --- | --- |
| `authentication` | Establishes who the actor is | Edge / `platform/` |
| `authorization` | `impl Can` for the action: may this actor do this, returning `Permit<G>` | In the slice, beside its action; checked at use-case entry, deny-by-default |
| `guard` | Enforcement point that *invokes* an authorization policy | Edge. MUST NOT contain the decision itself or any role conditional |

## Computation

(8 — separate calculation from interaction; the functional core)

| Role | Responsibility | Where it lives / caveat |
| --- | --- | --- |
| `calculator` | Encapsulated calculation | Functional core of the slice, or `policies/` when shared |
| `extractor` | Pulls information out of a larger structure | Slice |
| `selector` | Selects/derives a subset of data | Slice |

## Platform substrate

(7 — time, chance, identity, and configuration are inputs, so they are handed in from here rather than discovered) Business-free technical concerns: `config`, `logger`, `telemetry`, `clock` / `time-provider`, `id-generator`, `feature-flags`. These live in `platform/`, and ONLY once 2+ capabilities need them. Any of these that acquires business meaning MUST move to the owning capability (see `platform/` in `structure-and-boundaries.md`).

## Tests

Colocated with the slice they cover (see `testing-and-governance.md`). Supporting names: `fixtures` (static data), `builders` (test data construction), `fakes` (in-memory doubles). Cross-module tests only in the four canonical `tests/` buckets.

## `utils` and `helpers`

Both are legitimate names. Both are also a signal that the code has **no more specific architectural responsibility**. Preference ladder: specific role name → `utils` → `helpers`.

```text
❌ utils/validate.ts       ✅ parser.ts / schema.ts
❌ utils/parse.ts          ✅ parser.ts
❌ utils/transform.ts      ✅ mapper.ts
❌ helpers/save.ts         ✅ store.ts (narrow functions over the ORM)
❌ helpers/checkAccess.ts  ✅ refund-order/authorization.ts
```

The ledger rejects `utils`/`common` modules for cohabitation without a shared reason for change (13) — a module named for having no name. `utils` is tolerated for exactly the code that passes that test: small, generic, business-free, dependency-free functions with no reason to change at all — stdlib-shaped code with no owning capability (`platform/utils/`: `clamp`, `sleep`, `isDefined`, `groupBy`). Those belong in `platform/`, not at a module's top level, and the first entry with a business or infrastructure reason to change MUST move out.

`helpers` is reserved for **local, contextual** plumbing of one slice — reshaping that carries no rule — and MUST stay inside that slice (`create-order/helpers/`: `group-lines-by-sku`, `zip-lines-with-prices`).

A `utils` or `helpers` folder that accumulates business rules or calculations is a defect; the rules MUST move to a policy, a domain type, or the slice's functional core (`calculator`).

## Names to avoid

(13 — cohabitation without a shared reason for change; 3 — renaming without removing) You SHOULD NOT use: `manager`, bare `service` (`OrderService` doing everything), `common`, `shared`, `core`, `base`, `impl`, `misc`, `data`, `models`, `dto`. Each names a technical bucket rather than a responsibility, and each grows without limit because nothing is out of scope for it. Layer folders (`controllers/`, `services/`, `repositories/`) are forbidden (Module structure in `structure-and-boundaries.md`). A wrapper that only forwards to another wrapper (`Service → Manager → Repository → ORM`) is wrapper-on-wrapper ceremony (ledger-rejected): each layer an edge that deletes nothing.

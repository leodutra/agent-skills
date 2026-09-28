# Role Vocabulary (file and folder names)

The names a file or folder may carry, by the **role it plays**. (Keywords and the `(n)` / `(ledger)` tags: see SKILL.md.) Function, type, and event names follow SKILL.md's Naming; a file name names a role, so `handler.ts` is legitimate where `handle()` as a business operation is not.

## Rules

- Name by **responsibility**, not by technical kind. A file MUST NOT carry a role name it does not fulfil (`repository.ts` that wraps one ORM call is a `store`).
- A **catalog to pull from, not a tree to create**. Most slices need three or four of these names, ever; a slice whose folder mirrors its siblings role-for-role was copied, not designed.
- **Singular for a file, plural for a folder** of several: `validator.ts`, `policies/`. snake_case languages transliterate: `use_case.py`.
- **One role per file.** A file needing two role names SHOULD be split — or the names are wrong.
- These names live *inside* a module; top-level source folders stay business capabilities.
- A role name binds only where the obligation it discharges exists (`first-principles.md`, §The ladder of statements). The tag on each category names the deriving principle.

A name with no note lives in the slice and has no rule of its own.

## Input, output, and shape

(8 — one translation per crossing; 2 — structural reconstruction is not semantic proof) `schema`, `serializer`, `deserializer` (`codec` MAY name a symmetric, co-located pair), `formatter`, `mapper`, `normalizer`, `presenter` / `view-model` (read side).

- `parser` — the slice boundary; SHOULD produce domain types directly (parse, don't validate).
- `converter` — `domain/` when the types are domain types, else `platform/`.
- `sanitizer` — the trust boundary; MUST NOT be skipped as "simplification".
- `contract` — the shape published to external consumers, in `api/`; changing it is a breaking change.
- `translator` — maps a foreign model into our language, next to the `gateway` it protects.

## Validation

(1 — establish by transformation, not by inspection) `matcher`.

- `validator` — subordinate to `parser`, never a peer: it MUST yield typed domain values, NOT a boolean or error list that leaves the raw shape in play downstream. A `validator` called below the boundary is a defect.
- `specification` — rare; ONLY when composing predicates or driving queries (`domain-modeling.md`).

## Application (the slice)

(14, 11 — one business operation's orchestration in one place, often the natural consistency scope; ledger: use case) `query`, `resolver`.

- `handler` — the default slice entry point. `use-case` is a synonym: pick ONE per codebase (*convention*).
- `command` — intent to change state; conceptual only, MUST NOT be read as requiring CQRS.
- `middleware` — `platform/`, business-free (ledger: middleware pipeline).
- `saga` / `process-manager` — module level, Stage 3+, ONLY when a real workflow spans consistency scopes and can fail midway (`events-and-consistency.md`).
- `job` / `task` — MUST be idempotent (10) and owned by a lifetime (12).

## Domain

(1, 3, 4 — receipts, distinctions in the medium, representable matched to meaningful) newtype, `value-object`, and `errors` live in `domain/` (technical error primitives MAY live in `platform/`); `events` in the slice or `domain/`.

- `entity` — `domain/`; rich behavior ONLY on a SKILL.md trigger.
- `policy` — slice by default; `policies/` when shared by 2+ slices.
- `process` / `reaction` — reactive when-then logic; MUST NOT be called a policy.
- `factory` — `domain/`, ONLY when construction itself carries rules. `builder` — rare, ONLY for genuinely many optional parts.
- `domain-service` — `domain/`; prefer a pure function in the functional core first.

## Persistence

(6 — localized persistence authority; 11 — the consistency scope; 2 — trust follows custody) `migration` (module `migrations/` or repository level).

- `store` — the Stage-1 default, module level (SKILL.md, Repository vs. ORM). Parses rows into domain types (2).
- `repository` — ONLY on SKILL.md's condition; never one per table (ledger).
- `read-model`, `cache` — copies of a fact, under SKILL.md's Copy vs. single home. `cache` lives in `platform/`.
- `projection` — only where events already exist; MUST be idempotent (10).
- `unit-of-work` / `transaction` — imperative shell or `platform/`; drawn no larger than its invariants demand (11).
- `outbox` — ONLY under `events-and-consistency.md` §Dual writes.

## Integration

(2 — every crossing is a re-acquisition of knowledge; 13 — change-sensitivity contained at one translation point)

- `gateway` — the boundary to an external system, in our language; module or slice. `client` — behind the gateway, or `platform/`.
- `adapter` — ONLY where two real, existing interfaces meet (ledger).
- `port` — ONLY over a world dependency (SKILL.md, Interface vs. function).

## Messaging

(1 — execution leaves receipts; 10 — semantics invariant under duplication and reordering; 11) `event` = a domain fact that happened; `message` = the transport envelope carrying it. You MUST NOT use the words interchangeably (*convention*, motivated by 3). `event`, `event-publisher`.

- `event-handler` / `subscriber` — in the consuming slice; MUST be idempotent (10).
- `message-publisher` / `message-consumer` — `platform/`, business-free.

## Security

(7 — identity and permission are inputs; 6 — decisions live with the authority; 2 — evidence travels, acceptance cannot)

- `authentication` — edge / `platform/`.
- `authorization` — `impl Can` for the action, in the slice beside it (`authorization.md`).
- `guard` — edge enforcement point that *invokes* an authorization decision; MUST NOT contain the decision itself or any role conditional.

## Computation

(8 — separate calculation from interaction) `extractor` (pulls information out of a larger structure; a framework "extractor" is a `parser`), `selector`.

- `calculator` — the slice's functional core, or `policies/` when shared.

## Platform substrate

(7 — time, chance, identity, and configuration are inputs, handed in from here rather than discovered) `config`, `logger`, `telemetry`, `clock` / `time-provider`, `id-generator`, `feature-flags` live in `platform/`, ONLY once 2+ capabilities need them. Any that acquires business meaning MUST move to the owning capability.

## Tests

Colocated with the slice they cover; cross-module tests only in the four `tests/` buckets (`testing-and-governance.md`). Supporting names: `fixtures` (static data), `builders` (test data construction), `fakes` (in-memory doubles).

## `utils` and `helpers`

Both are legitimate names, and both signal code with **no more specific responsibility**. Preference ladder: specific role name → `utils` → `helpers`.

```text
❌ utils/validate.ts       ✅ parser.ts / schema.ts
❌ utils/transform.ts      ✅ mapper.ts
❌ helpers/save.ts         ✅ store.ts
❌ helpers/checkAccess.ts  ✅ refund-order/authorization.ts
```

`utils` is tolerated for exactly the code that passes the ledger's `utils`/`common` test (13): small, generic, business-free, dependency-free functions with no reason to change (`platform/utils/`: `clamp`, `sleep`, `isDefined`, `groupBy`). The first entry with a business or infrastructure reason to change MUST move out.

`helpers` is reserved for **local** plumbing of one slice that carries no rule, and MUST stay inside that slice (`create-order/helpers/`: `group-lines-by-sku`).

A `utils` or `helpers` folder that accumulates business rules or calculations is a defect; the rules MUST move to a policy, a domain type, or the slice's `calculator`.

## Names to avoid

(13 — cohabitation without a shared reason for change; 3 — renaming without removing) You SHOULD NOT use: `manager`, bare `service` (`OrderService` doing everything), `common`, `shared`, `core`, `base`, `impl`, `misc`, `data`, `models`, `dto`. Each names a technical bucket rather than a responsibility, and grows without limit because nothing is out of scope for it. A wrapper that only forwards to another wrapper (`Service → Manager → Repository → ORM`) is wrapper-on-wrapper ceremony (ledger-rejected).

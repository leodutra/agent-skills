---
name: architecture-blueprint
description: Apply the Modern Architecture Blueprint (2026), a pragmatic domain-first method for designing long-lived software systems, derived from first principles (design as the assignment of proof obligations). Covers modular monoliths, vertical-slice feature folders, type-driven domain modeling (newtypes, value objects, parse-don't-validate, make-illegal-states-unrepresentable), policies, domain events, explicit consistency scopes, idempotency, functional-core/imperative-shell, architecture fitness functions, and ADRs. Use this skill whenever the user is designing, scaffolding, structuring, refactoring, or reviewing the architecture of a backend or full-stack system; deciding folder or module layout; weighing abstractions like repositories, CQRS, microservices, or event sourcing; modeling a business domain; deciding how modules should communicate; or asking why an architectural rule or pattern holds. Trigger it for questions like "how should I structure this service", "where should this code live", or "is this over-engineered" even when the word architecture is never used. Especially relevant for TypeScript/Node, Rust, and Python services.
---

# Modern Architecture Blueprint

Domain-first method for long-lived systems. Prefer business capabilities over technical layers, locality over abstraction, and strong types over runtime checks. This skill is the decision layer. You MUST read the matching reference file before applying a pattern in depth.

Core rule: **every abstraction MUST earn its existence.** An obligation must exist before it is assigned; a proof nobody relies on is negative work (`references/first-principles.md`, §The frame). You MUST treat the pattern catalog as pull-based, not a checklist.

Every rule in this skill is a consequence of `references/first-principles.md`. A tag such as `(1, 8)` names the principles a rule derives from, `(frame)` the proof-obligation frame, `(A1–A4)` its foundations, `(ledger)` the pattern-ledger entry that carries a pattern's conditions. Challenge a rule through its derivation, never by importing a competing pattern.

## Normative keywords

- **MUST / MUST NOT** — non-negotiable; violating it is a defect. Either a requirement derived from a principle, or a *convention* this skill stipulates for consistency and labels as such.
- **SHOULD / SHOULD NOT** — strong default (a heuristic); deviate ONLY with a stated, demonstrated reason, and ONLY for an exception this skill explicitly names.
- **MAY** — a genuine option with no default preference.
- **CANNOT** — a fact the type system or runtime enforces; not a choice.

You MUST NOT invent exceptions to a SHOULD beyond those named in this skill. When unsure, follow the SHOULD.

A pattern's *name* is never a MUST. Patterns implement requirements and bind only under the conditions their ledger entry states (§The ladder of statements). Enforcing one by name — "always use a repository" — is a level violation, and you MUST flag it as a defect exactly like an unearned abstraction.

## How to use

- **New system** → apply North Star + Core Principles, lay out modules per `references/structure-and-boundaries.md`, and apply ONLY Stage 1 of the Evolution Path.
- **Focused design question** → use Decision Rules, then open the matching reference.
- **Reviewing code/design** → use the Review Checklist.
- **Modeling a concept** → read `references/domain-modeling.md`.
- **Novel tradeoff no decision rule covers, or a "why" dispute** → derive the answer from `references/first-principles.md` instead of importing a pattern; its ledger gives each pattern's derivation and conditions.

**Record decisions as you go.** When you conclude a considerable architectural decision or definition, you MUST record it as an ADR — or explicitly propose one — and MUST keep ADRs maintained (13, 1 — a design decision is a framed fact; unrecorded, it reverts to unknown for every later maintainer). See `references/testing-and-governance.md`.

## North Star

Priority order: (1) **Correctness** — illegal states hard to reach (4); (2) **Comprehensibility** — every important property checkable locally (14); (3) **Changeability** — low sensitivity to the changes that actually happen (13); (4) **AI navigability** — the maintainer is a bounded reasoner, human or machine (A1); (5) **Operational simplicity** — outside the framework's scope (§The limits of the framework itself) and stipulated here on its own merit.

The first four serve one objective: minimize the lifetime cost of keeping the system's propositions true (14). The fifth is added because a system nobody can run is not maintained either.

You MUST NOT optimize for: maximum abstraction (3 — an abstraction must remove possibilities, not rename them), framework independence or speculative future-proofing (13 — insure against probable change, not imaginable change), theoretical purity (frame — an obligation must exist before it is assigned), or maximum reuse (13 — sameness is sameness of reason, not of text).

## Core principles

The fourteen principles compress to three reductions and one direction of flow (§Compression). These are those reductions applied to code:

**Reduce possibility** (1, 3, 4, 12)

- **Establish once, carry the receipt.** Parse at the boundary into types that prove their own validity, and enclose each resource's lifetime in its owner's; nothing downstream re-checks validity or liveness. Type-driven modeling is on from Stage 1.
- **Distinctions live in the medium.** Where correctness turns on a difference, the types differ. Names, comments, and READMEs are testimony, not enforcement.
- **Prefer deletion.** Before adding any abstraction, ask "can this be solved with fewer concepts?" An abstraction that renames possibilities without removing any has not earned its place.

**Reduce interaction** (5, 6, 7)

- **Narrow edges, explicit inputs.** Modules expose one narrow API. Slices receive the narrowest capability they need, never a database handle or god object, and nothing reaches for ambient state, the clock, or configuration. Concrete infrastructure MUST be wired in a single composition root; business code receives dependencies and MUST NOT construct them.
- **One owner per mutable fact.** Every piece of mutable state, and every business rule, has one nameable authoritative home. A second copy is a coherence obligation that MUST be priced: whatever appears eliminated has been moved (A3).
- **Compose, don't inherit.** You MUST NOT build business behavior through inheritance hierarchies (`BaseService → AbstractService → ConcreteService`): a subclass couples implicitly to the whole base behavior (5), and the chain must be read end-to-end before any method can be trusted (14). Compose small types, functions, traits/interfaces, generics, and enums instead. Extending a base class a framework requires is a technique, not a design.

**Reduce propagation** (8, 9, 10, 11, 13)

- **Domain first.** Within the application source tree (for example, `src/`), top-level folders MUST be business capabilities (`orders/`, `billing/`…). The ONLY sanctioned non-capability source-tree entries are optional `platform/` (genuinely cross-cutting, business-free technical substrate) and `tests/` (cross-module tests). Repository-level support folders such as `docs/adr/` and, in Rust repositories, `xtask/` MAY exist alongside the source tree. Any other technical-concern source-tree folder is a defect. (*Convention*; the requirement it implements is coupling by shared reason for change, 13.)
- **Locality over layering.** Feature folders (`orders/refund-order/`), never technical-layer folders (`controllers/`, `services/`, `repositories/`) at any level (*convention*; 13, 14). Code that changes together lives together; navigate by business behavior.
- **Resolve at the perimeter.** Uncertainty about data collapses at the edge, once; the interior reasons over knowns. Failure is translated at each boundary into the receiver's vocabulary — never leaked raw, never swallowed.
- **Absorb the environment with semantics.** Where delivery can repeat, reorder, or stop halfway, operations are idempotent, bounded, and inside a declared consistency scope.

**One direction of flow** (§Compression)

- **Simplicity until complexity appears.** Correctness migrates toward construction; design commitments migrate toward evidence, because the designer's knowledge grows over the system's life (13). You MUST NOT introduce a pattern without a present, demonstrated need (see Avoid by default). The Evolution Path is this gradient made operational.

## Evolution Path (central decision tool)

You SHOULD stay at the earliest stage that meets current needs and advance ONLY on a concrete trigger (13 — escalate structure on evidence rather than anticipation; 8 — design uncertainty collapses late). When unsure, default to the lower stage and state why.

1. **Foundation** — modules + vertical slices (feature folders) + newtypes for identity + parse-don't-validate at the boundary. Most projects stay here.
2. **Concepts with rules** — add value objects and shared decision logic (policies) as rules accumulate and slices duplicate them (6 — one authoritative home per piece of knowledge).
3. **Rich behavior (escalation)** — move behavior onto domain objects and add domain events ONLY on a trigger (see Vertical slice vs. rich domain object). Slices remain the default home for logic.
4. **Enforcement** — add architecture fitness functions and stronger isolation when boundaries need policing (frame, rung 2).
5. **Service extraction** — split a module into a service ONLY when operational reality (scaling, ownership, deployment) demands it. A service boundary is a frame crossing paid on every call over an environment that can duplicate, reorder, and drop (2, 10); microservices are an optimization, not a start.

Type-driven modeling (newtypes, value objects, illegal-states-unrepresentable) is on from Stage 1 — it MUST NOT be treated as an escalation.

## Decision rules

- **Direct call vs. event** (11, 5) — decide the consistency scope first, then coupling. SHOULD use a direct call when same transaction / same invariant / immediate consistency. SHOULD use an event when another module merely reacts, eventual consistency is acceptable, and coupling should drop. See `references/events-and-consistency.md`.
- **Repository vs. ORM** (6, 5; ledger) — SHOULD call the ORM/query builder directly by default (`orm.orders.create(...)`), from the narrow persistence function the slice names and receives (`loadOrder`, `saveOrder` — the `store` role); no repository object between that function and the ORM. Introduce a repository ONLY when it models a domain persistence boundary: aggregate-shaped load/save with rules of its own, query reuse across slices, or a real planned storage swap — never one per table. See `references/domain-modeling.md`.
- **Interface vs. function** (5, 7, 13; ledger) — a dependency on the world (persistence, network, clock, randomness, queue) MUST enter the slice as an explicit capability. Being the world is what earns the seam: the test double that stands in for it is the second implementation. Shape follows need — one operation is a function type, a bundle that travels together is a trait/interface. You MUST NOT put an interface over pure in-process code with no world behind it. See `references/structure-and-boundaries.md`.
- **Newtype vs. value object** (3, 1, 4) — use a newtype when two same-typed primitives could be swapped (ids). Use a value object when the concept carries validation/invariants/behavior (Money, Email, Percentage). See `references/domain-modeling.md`.
- **Policy vs. specification** (6, 1, 5) — a **policy** is the default home for a business decision; it bundles related decisions/calculations (`refundPolicy.isRefundable(order)`, `refundPolicy.refundAmount(order)`; `can*` names are reserved for authorization). Use a **specification** (composable `isSatisfiedBy` predicate) ONLY when actually composing predicates or driving queries; otherwise a method/function (`customer.isEligible()`) SHOULD be preferred. The `policies/` folder SHOULD appear only when decision logic is shared by 2+ slices — EXCEPT authorization `can*` policies, which MAY be grouped there even when slice-specific (auditability; see `references/authorization.md`). See `references/domain-modeling.md`.
- **Vertical slice vs. rich domain object** (13, 14; triggers from 11, 6, 4, 12) — default: logic in the slice + functional core. Move behavior onto an object (`order.cancel()`) ONLY on a trigger: (a) many rules cluster on one entity; (b) an invariant spans multiple operations — the object is then the invariant's consistency scope, drawn no larger than the invariant demands; (c) real lifecycle/state machine with illegal transitions; (d) same invariant enforced from 2+ slices — one authoritative home; (e) high cost of violation (money, inventory, compliance). Absent a trigger, a rich object is over-engineering and SHOULD NOT be introduced.
- **Copy vs. single home** (6, 2) — a cache, read model, or denormalized column is a second copy of a fact. It MAY exist ONLY with a named authoritative home, a stated staleness bound, and a measured need. See `references/events-and-consistency.md`.
- **Authorization** (7, 6, 2, 1) — gate by capability; you MUST NOT use role conditionals (`if role == "admin"`). Authorization MUST be a `can*` domain policy — a pure function of `actor` + resource (full context) — checked at **use-case entry**, deny-by-default. The entity guards business invariants; the policy guards who-may-act. Authorization MUST NOT live on the entity. Roles are capability groupings assigned at the edge. See `references/authorization.md`.
- **One file vs. feature folder** (13) — a small feature MAY start as a single file (`refundOrder.ts`) and grow into a folder when it earns it. You SHOULD NOT pre-split.

## Pattern map → where to read

| You are working on… | Read |
| --- | --- |
| Folder/module layout, module public APIs, dependency direction, READMEs, file/folder role names (`handler`, `mapper`, `store`, `gateway`, `utils`…), anti-corruption boundaries, composition root, capability dependencies and seams, state ownership and lifetimes | `references/structure-and-boundaries.md` |
| Newtypes, value objects, parse-don't-validate, typed config, illegal states, absence, exhaustiveness, lifecycle typestate, error taxonomy, policies, rich domain objects, functional core, temporal modeling, idempotency, persistence | `references/domain-modeling.md` |
| Domain events, event naming and versioning, direct-call vs event, consistency scopes, outbox, sagas, copies and caches, cancellation, bounded concurrency, retries and backpressure, scatter-gather, observability | `references/events-and-consistency.md` |
| Unit/integration/acceptance tests, property and contract tests, test placement, fitness functions, ADRs, AI context files | `references/testing-and-governance.md` |
| Authorization, access control, permissions vs. roles, deny-by-default | `references/authorization.md` |
| Justifying or challenging any rule; a situation no rule covers; two rules in tension; the pattern ledger (each pattern's derivation and conditions); proof obligations, validity frames, consistency scopes, local checkability; the nine tests | `references/first-principles.md` |

## Naming

Names MUST speak the business language: `approveOrder()`, `reserveInventory()`, `calculateShippingCost()` (14 — understandability is load-bearing). You SHOULD NOT use vague verbs (`process`, `execute`, `run`, `handle`) unless intent is obvious from context. Events MUST be past-tense business facts (`OrderApproved`, `InventoryReserved`) and MUST NOT be vague mutations (`OrderUpdated`, `EntityChanged`) — *convention*, motivated by 1: a receipt that does not say what happened is not a receipt. `can*` is reserved for authorization policies; business eligibility reads `isRefundable`, `isEligible`. A name is testimony (3): it informs the reader and enforces nothing, so a name never substitutes for a type.

File and folder names are a separate axis: they name the **role** a file plays (`handler`, `parser`, `mapper`, `store`, `gateway`), which is why a generic word is acceptable there and not in a business operation name. You MUST name a file for its actual responsibility, and SHOULD fall back to `utils` (business-free generics, in `platform/`) or slice-local `helpers/` ONLY when no specific role fits. See the role vocabulary in `references/structure-and-boundaries.md`.

## Avoid by default

Without a present, demonstrated need, each of these is a defect under the earn-it rule (Core principles): microservices first, repositories everywhere, CQRS everywhere, event sourcing everywhere, layer-based folders, factory proliferation, specification proliferation, framework-centric architecture.

Rejected by derivation (ledger) — defects under any need: service locator (7); ambient singleton / global state (7, 6); god context objects passed everywhere (5, 6); interface-for-everything (13, 5); `utils`/`common` modules holding anything with a reason to change (13); wrapper-on-wrapper ceremony (3).

## Review checklist

1. **Organization** (13, 14) — Within the application source tree, are top-level folders business capabilities (the ONLY allowed non-capability entries being optional `platform/` and `tests/`)? Are features vertical slices, with no technical-layer folders at any level? Does code that changes together live together? Does each file's name state its actual role, with `utils`/`helpers` used only where no specific role fits?
2. **Boundaries** (5, 6, 2) — Narrow module public API (`orders/api`)? No module reaching into another's internals — including its tables and event internals? Dependencies explicit and acyclic, with the composition root outside `platform/`? Do slices receive narrow capabilities rather than a database handle or god service? Do foreign models stop at a gateway/translator? Authorization a `can*` policy at use-case entry (deny-by-default), kept OUT of entities, never scattered role conditionals?
3. **Inputs** (7) — Does any core function read the clock, environment, randomness, or global state instead of receiving it? Any service locator, ambient singleton, or configuration looked up at point of use?
4. **Types** (1, 3, 4, 9) — Identities are newtypes? Rule-bearing concepts are value objects? Both under `domain/`? Parsing done once at the boundary, config included, and does every check change the representation rather than pass the raw value on? Strong types kept, not unwrapped to primitives for convenience? Illegal states unrepresentable via closed, exhaustively matched unions? Absence modeled as a state, not a sentinel? Errors classified (domain / application / infrastructure / transport) and translated at each boundary rather than leaked or swallowed?
5. **Behavior** (6, 11) — Logic in slice + functional core by default? Behavior centralized on an object ONLY on a named trigger (flag rich objects that have not earned it), and no larger than its invariant demands? Shared `policies/` genuinely shared by 2+ slices (authorization `can*` policies excepted) and distinct from reactive processes?
6. **Communication & consistency** (11, 10, 6, 13) — Each interaction's consistency scope declared? Events past-tense business facts with additive, versioned payloads? Externally triggered commands idempotent? Dual writes go through an outbox or an explicit loss decision? Cross-scope changes model their intermediate states? Every copy of a fact has a named home and a staleness bound? Retries under one policy, queues and fan-out bounded, overload pushed backward?
7. **Time & lifetime** (2, 12) — Temporal facts explicit (`approvedAt`, `shippedAt`) where rules depend on them, not inferred from `status`? Resources scope-bound, spawned work owned by its initiator, cancellation reaching it? Framed facts (tokens, leases, cached permissions) carry their expiry?
8. **Governance** (frame, rungs 2–3) — From Stage 4, rules enforced by fitness functions, not just docs? Important workflows observable with correlation IDs, emitted for a named audience? Considerable decisions recorded as ADRs and kept maintained? `AGENTS.md`/`ARCHITECTURE.md` present? Tests placed by scope — single-module tests (unit, integration, AND slice-scoped acceptance) colocated, and only cross-module behavior in `tests/` (canonical buckets: `acceptance/`, `architecture/`, `e2e/`, `performance/`)?
9. **Restraint** (frame, 5, 3) — Any abstraction that has not earned its place (premature repositories, specifications, rich objects, CQRS)? Any pattern present by name rather than by the obligation it discharges? Could the design use fewer concepts?

For a contested or novel call, apply the nine tests in `references/first-principles.md` (§The tests) before ruling, then the meta-test: ban the pattern's name and reconstruct it from the principles alone — what cannot be reconstructed is ritual.

You MUST flag over-engineering as readily as under-engineering. Recommend the lowest Evolution Path stage that meets the actual requirements, and name the concrete trigger that would justify advancing.

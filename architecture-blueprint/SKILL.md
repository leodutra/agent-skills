---
name: architecture-blueprint
description: Apply the Modern Architecture Blueprint (2026), a pragmatic domain-first method for designing long-lived software systems. Covers modular monoliths, vertical-slice feature folders, type-driven domain modeling (newtypes, value objects, parse-don't-validate, make-illegal-states-unrepresentable), policies, domain events, explicit consistency models, idempotency, functional-core/imperative-shell, architecture fitness functions, and ADRs. Use this skill whenever the user is designing, scaffolding, structuring, refactoring, or reviewing the architecture of a backend or full-stack system; deciding folder or module layout; weighing abstractions like repositories, CQRS, microservices, or event sourcing; modeling a business domain; or deciding how modules should communicate. Trigger it for questions like "how should I structure this service", "where should this code live", or "is this over-engineered" even when the word architecture is never used. Especially relevant for TypeScript/Node, Rust, and Python services.
---

# Modern Architecture Blueprint

Domain-first method for long-lived systems. Prefer business capabilities over technical layers, locality over abstraction, and strong types over runtime checks. This skill is the decision layer. You MUST read the matching reference file before applying a pattern in depth.

Core rule: **every abstraction MUST earn its existence.** You MUST treat the pattern catalog as pull-based, not a checklist.

## Normative keywords

- **MUST / MUST NOT** — non-negotiable; violating it is a defect.
- **SHOULD / SHOULD NOT** — strong default; deviate ONLY with a stated, demonstrated reason, and ONLY for an exception this skill explicitly names.
- **MAY** — a genuine option with no default preference.
- **CANNOT** — a fact the type system or runtime enforces; not a choice.

You MUST NOT invent exceptions to a SHOULD beyond those named in this skill. When unsure, follow the SHOULD.

## How to use

- **New system** → apply North Star + Core Principles, lay out modules per `references/structure-and-boundaries.md`, and apply ONLY Stage 1 of the Evolution Path.
- **Focused design question** → use Decision Rules, then open the matching reference.
- **Reviewing code/design** → use the Review Checklist.
- **Modeling a concept** → read `references/domain-modeling.md`.

**Record decisions as you go.** When you conclude a considerable architectural decision or definition, you MUST record it as an ADR — or explicitly propose one — and MUST keep ADRs maintained. See `references/testing-and-governance.md`.

## North Star

Priority order: (1) **Correctness** — illegal states hard to reach; (2) **Comprehensibility**; (3) **Changeability**; (4) **AI navigability**; (5) **Operational simplicity**.

You MUST NOT optimize for: maximum abstraction, framework independence, theoretical purity, maximum reuse, or speculative future-proofing.

## Core principles

- **Optimize for change.** Structure around what changes together.
- **Locality over layering.** SHOULD prefer feature folders (`orders/refund-order/`) over technical layers (`controllers/`, `services/`). Navigate by business behavior.
- **Domain first.** Within the application source tree (for example, `src/`), top-level folders MUST be business capabilities (`orders/`, `billing/`…). The ONLY sanctioned non-capability source-tree entries are optional `platform/` (genuinely cross-cutting, business-free technical substrate) and `tests/` (cross-module tests). Repository-level support folders such as `docs/adr/` and, in Rust repositories, `xtask/` MAY exist alongside the source tree. Any other technical-concern source-tree folder is a defect.
- **Simplicity until complexity appears.** You MUST NOT introduce repositories, factories, CQRS, event sourcing, microservices, or specification hierarchies without a present, demonstrated need.
- **Prefer deletion.** Before adding any abstraction, ask "can this be solved with fewer concepts?"

## Evolution Path (central decision tool)

You SHOULD stay at the earliest stage that meets current needs and advance ONLY on a concrete trigger. When unsure, default to the lower stage and state why.

1. **Foundation** — modules + vertical slices (feature folders) + newtypes for identity + parse-don't-validate at the boundary. Most projects stay here.
2. **Concepts with rules** — add value objects and shared decision logic (policies) as rules accumulate and slices duplicate them.
3. **Rich behavior (escalation)** — move behavior onto domain objects and add domain events ONLY on a trigger (see vertical-slice rule). Slices remain the default home for logic.
4. **Enforcement** — add architecture fitness functions and stronger isolation when boundaries need policing.
5. **Service extraction** — split a module into a service ONLY when operational reality (scaling, ownership, deployment) demands it. Microservices are an optimization, not a start.

Type-driven modeling (newtypes, value objects, illegal-states-unrepresentable) is on from Stage 1 — it MUST NOT be treated as an escalation.

## Decision rules

- **Direct call vs. event** — SHOULD use a direct call when same transaction / same invariant / immediate consistency. SHOULD use an event when another module merely reacts, eventual consistency is acceptable, and coupling should drop. See `references/events-and-consistency.md`.
- **Repository vs. ORM** — SHOULD call the ORM/query builder directly by default (`orm.orders.create(...)`). Introduce a repository ONLY for measurable value (complex query reuse, a real planned storage swap).
- **Newtype vs. value object** — use a newtype when two same-typed primitives could be swapped (ids). Use a value object when the concept carries validation/invariants/behavior (Money, Email, Percentage). See `references/domain-modeling.md`.
- **Policy vs. specification** — a **policy** is the default home for a business decision; it bundles related decisions/calculations (`refundPolicy.canRefund(order)`, `refundPolicy.refundAmount(order)`). Use a **specification** (composable `isSatisfiedBy` predicate) ONLY when actually composing predicates or driving queries (~10–20 policies per spec); otherwise a method/function (`customer.isEligible()`) SHOULD be preferred. The `policies/` folder SHOULD appear only when decision logic is shared by 2+ slices — EXCEPT authorization `can*` policies, which MAY be grouped there even when slice-specific (auditability; see `references/authorization.md`). See `references/domain-modeling.md`.
- **Vertical slice vs. rich domain object** — default: logic in the slice + functional core. Move behavior onto an object (`order.cancel()`) ONLY on a trigger: (a) many rules cluster on one entity; (b) an invariant spans multiple operations; (c) real lifecycle/state machine with illegal transitions; (d) same invariant enforced from 2+ slices; (e) high cost of violation (money, inventory, compliance). Absent a trigger, a rich object is over-engineering and SHOULD NOT be introduced.
- **Authorization** — gate by capability; you MUST NOT use role conditionals (`if role == "admin"`). Authorization MUST be a `can*` domain policy — a pure function of `actor` + resource (full context) — checked at **use-case entry**, deny-by-default. The entity guards business invariants; the policy guards who-may-act. Authorization MUST NOT live on the entity. Roles are capability groupings assigned at the edge. See `references/authorization.md`.
- **One file vs. feature folder** — a small feature MAY start as a single file (`refundOrder.ts`) and grow into a folder when it earns it. You SHOULD NOT pre-split.

## Pattern map → where to read

| You are working on… | Read |
| --- | --- |
| Folder/module layout, module public APIs, dependency direction, READMEs | `references/structure-and-boundaries.md` |
| Newtypes, value objects, parse-don't-validate, illegal states, policies, rich domain objects, functional core, temporal modeling, idempotency, persistence | `references/domain-modeling.md` |
| Domain events, event naming, direct-call vs event, consistency model, observability | `references/events-and-consistency.md` |
| Unit/integration/acceptance tests, test placement, fitness functions, ADRs, AI context files | `references/testing-and-governance.md` |
| Authorization, access control, permissions vs. roles, deny-by-default | `references/authorization.md` |

## Naming

Names MUST speak the business language: `approveOrder()`, `reserveInventory()`, `calculateShippingCost()`. You SHOULD NOT use vague verbs (`process`, `execute`, `run`, `handle`) unless intent is obvious from context. Events MUST be past-tense business facts (`OrderApproved`, `InventoryReserved`) and MUST NOT be vague mutations (`OrderUpdated`, `EntityChanged`).

## Avoid by default

You SHOULD NOT introduce these without a present, demonstrated need: microservices first, repositories everywhere, CQRS everywhere, event sourcing everywhere, layer-based folders, factory proliferation, specification proliferation, framework-centric architecture.

## Review checklist

1. **Organization** — Within the application source tree, are top-level folders business capabilities (the ONLY allowed non-capability entries being optional `platform/` and `tests/`)? Are features vertical slices? Does code that changes together live together?
2. **Boundaries** — Narrow module public API (`orders/api`)? No module reaching into another's internals? Dependencies explicit and acyclic? Authorization a `can*` policy at use-case entry (deny-by-default), kept OUT of entities, never scattered role conditionals?
3. **Types** — Identities are newtypes? Rule-bearing concepts are value objects? Both under `domain/`? Validation done once at the boundary? Illegal states unrepresentable via typed unions?
4. **Behavior** — Logic in slice + functional core by default? Behavior centralized on an object ONLY on a named trigger (flag rich objects that have not earned it)? Shared `policies/` genuinely shared by 2+ slices (authorization `can*` policies excepted) and distinct from reactive processes?
5. **Communication & consistency** — Each interaction's consistency declared? Events past-tense business facts? Externally triggered commands idempotent?
6. **Time** — Temporal facts explicit (`approvedAt`, `shippedAt`) where rules depend on them, not inferred from `status`?
7. **Governance** — Rules enforced by fitness functions, not just docs? Important workflows observable with correlation IDs? Considerable decisions recorded as ADRs and kept maintained? `AGENTS.md`/`ARCHITECTURE.md` present? Tests placed by scope — single-module tests (unit, integration, AND slice-scoped acceptance) colocated, and only cross-module behavior in `tests/` (canonical buckets: `acceptance/`, `architecture/`, `e2e/`, `performance/`)?
8. **Restraint** — Any abstraction that has not earned its place (premature repositories, specifications, rich objects, CQRS)? Could the design use fewer concepts?

You MUST flag over-engineering as readily as under-engineering. Recommend the lowest Evolution Path stage that meets the actual requirements, and name the concrete trigger that would justify advancing.

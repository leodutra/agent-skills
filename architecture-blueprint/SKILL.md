---
name: architecture-blueprint
description: Apply the Modern Architecture Blueprint (2026), a pragmatic domain-first method for designing long-lived software systems. Covers modular monoliths, vertical-slice feature folders, type-driven domain modeling (newtypes, value objects, parse-don't-validate, make-illegal-states-unrepresentable), policies, domain events, explicit consistency models, idempotency, functional-core/imperative-shell, architecture fitness functions, and ADRs. Use this skill whenever the user is designing, scaffolding, structuring, refactoring, or reviewing the architecture of a backend or full-stack system; deciding folder or module layout; weighing abstractions like repositories, CQRS, microservices, or event sourcing; modeling a business domain; or deciding how modules should communicate. Trigger it for questions like "how should I structure this service", "where should this code live", or "is this over-engineered" even when the word architecture is never used. Especially relevant for TypeScript/Node, Rust, and Python services.
---

# Modern Architecture Blueprint

Domain-first method for long-lived systems, optimized for humans and AI agents. Favors business capabilities over technical layers, locality over abstraction, strong types over runtime checks. This skill is the decision layer; detailed patterns live in `references/` — read the matching file before applying a pattern in depth.

Core rule: **every abstraction must earn its existence.** The pattern catalog is a menu pulled from on demand, never a checklist to build up front.

## How to use

- **New system** → North Star + Core Principles, lay out modules per `references/structure-and-boundaries.md`, apply only Stage 1 of the Evolution Path.
- **Focused design question** → use Decision Rules, open the matching reference.
- **Reviewing code/design** → Review Checklist.
- **Modeling a concept** → `references/domain-modeling.md`.

## North Star

Priority order: (1) **Correctness** — illegal states hard to reach; (2) **Comprehensibility**; (3) **Changeability**; (4) **AI navigability**; (5) **Operational simplicity**.

Do **not** optimize for: maximum abstraction, framework independence, theoretical purity, maximum reuse, speculative future-proofing. Real work is adding features and changing rules, not swapping databases or frameworks — make the common case cheap.

## Core principles

- **Optimize for change.** Structure around what changes together.
- **Locality over layering.** Prefer feature folders (`orders/refund-order/`) over technical layers (`controllers/`, `services/`). Navigate by business behavior.
- **Domain first.** Top-level folders are business capabilities (`orders/`, `billing/`…), never technical concerns.
- **Simplicity until complexity appears.** No repositories, factories, CQRS, event sourcing, microservices, or specification hierarchies without present need.
- **Prefer deletion.** Ask "can this be solved with fewer concepts?" before adding any abstraction.

## Evolution Path (central decision tool)

Stay at the earliest stage that meets current needs; advance only on a concrete trigger. When unsure, default to the lower stage and say why.

1. **Foundation** — modules + vertical slices (feature folders) + newtypes for identity + parse-don't-validate at the boundary. Most projects stay here.
2. **Concepts with rules** — add value objects and shared decision logic (policies) as rules accumulate and slices duplicate them.
3. **Rich behavior (escalation)** — move behavior onto domain objects and add domain events, only on a trigger (see vertical-slice rule). Slices stay the default home for logic.
4. **Enforcement** — add architecture fitness functions and stronger isolation when boundaries need policing.
5. **Service extraction** — split a module into a service only when operational reality (scaling, ownership, deployment) demands it. Microservices are an optimization, not a start.

Type-driven modeling (newtypes, value objects, illegal-states-unrepresentable) is on from Stage 1 — not an escalation.

## Decision rules

- **Direct call vs. event** — direct call when same transaction / same invariant / immediate consistency; event when another module merely reacts, eventual consistency is fine, and coupling should drop. See `references/events-and-consistency.md`.
- **Repository vs. ORM** — call the ORM/query builder directly by default (`orm.orders.create(...)`). Add a repository only for measurable value (complex query reuse, a real planned storage swap).
- **Newtype vs. value object** — newtype when two same-typed primitives could be swapped (ids). Value object when the concept carries validation/invariants/behavior (Money, Email, Percentage). See `references/domain-modeling.md`.
- **Policy vs. specification** — a **policy** is the default home for a business decision; it bundles related decisions/calculations (`refundPolicy.canRefund(order)`, `refundPolicy.refundAmount(order)`). Use a **specification** (composable `isSatisfiedBy` predicate) only when actually composing predicates or driving queries (~10–20 policies per spec); else a method/function (`customer.isEligible()`) beats it. The `policies/` folder appears only when logic is shared by 2+ slices. See `references/domain-modeling.md`.
- **Vertical slice vs. rich domain object** — default: logic in the slice + functional core. Move behavior onto an object (`order.cancel()`) only on a trigger: (a) many rules cluster on one entity; (b) an invariant spans multiple operations; (c) real lifecycle/state machine with illegal transitions; (d) same invariant enforced from 2+ slices; (e) high cost of violation (money, inventory, compliance). Else it is over-engineering.
- **Authorization** — gate by capability, never role conditionals (`if role == "admin"`). Authorization is a `can*` domain policy — a pure function of `actor` + resource (full context) — checked at **use-case entry**, deny-by-default. The entity guards business invariants; the policy guards who-may-act (keep authz out of the entity). Roles are capability groupings assigned at the edge. See `references/authorization.md`.
- **One file vs. feature folder** — start small (`refundOrder.ts`), grow into a folder when it earns it. Don't pre-split.

## Pattern map → where to read

| You are working on… | Read |
| --- | --- |
| Folder/module layout, module public APIs, dependency direction, READMEs | `references/structure-and-boundaries.md` |
| Newtypes, value objects, parse-don't-validate, illegal states, policies, rich domain objects, functional core, temporal modeling, idempotency, persistence | `references/domain-modeling.md` |
| Domain events, event naming, direct-call vs event, consistency model, observability | `references/events-and-consistency.md` |
| Unit/integration/acceptance tests, test colocation, fitness functions, ADRs, AI context files | `references/testing-and-governance.md` |
| Authorization, access control, permissions vs. roles, deny-by-default | `references/authorization.md` |

## Naming

Names speak the business language: `approveOrder()`, `reserveInventory()`, `calculateShippingCost()`. Avoid vague verbs (`process`, `execute`, `run`, `handle`) unless intent is obvious. Events are past-tense business facts (`OrderApproved`, `InventoryReserved`), never vague mutations (`OrderUpdated`, `EntityChanged`).

## Avoid by default

Smells unless a present need justifies them: microservices first, repositories everywhere, CQRS everywhere, event sourcing everywhere, layer-based folders, factory proliferation, specification proliferation, framework-centric architecture.

## Review checklist

1. **Organization** — top-level folders are business capabilities, not layers? features as vertical slices? code that changes together lives together?
2. **Boundaries** — narrow module public API (`orders/api`)? no reaching into internals? explicit acyclic dependencies? authorization as a `can*` policy at use-case entry (deny-by-default), kept out of entities, not scattered role conditionals?
3. **Types** — identities are newtypes? rule-bearing concepts are value objects? both under `domain/`? validation once at the boundary? illegal states unrepresentable via typed unions?
4. **Behavior** — logic in slice + functional core by default? behavior centralized on an object only on a trigger? any rich objects that haven't earned it? shared `policies/` genuinely shared by 2+ slices and distinct from reactive processes?
5. **Communication & consistency** — each interaction's consistency declared? events past-tense business facts? externally triggered commands idempotent?
6. **Time** — temporal facts explicit (`approvedAt`, `shippedAt`) where rules depend on them, not inferred from `status`?
7. **Governance** — rules enforced by fitness functions, not just docs? important workflows observable with correlation IDs? key decisions in ADRs? `AGENTS.md`/`ARCHITECTURE.md` present? unit/integration tests colocated, only e2e/architecture/performance centralized?
8. **Restraint** — any abstraction that hasn't earned its place (premature repositories, specifications, rich objects, CQRS)? fewer concepts possible?

Flag over- and under-engineering equally. Recommend the lowest Evolution Path stage that meets requirements, and name the trigger that would justify advancing.

---
name: architecture-blueprint
description: Apply the Modern Architecture Blueprint (2026), a pragmatic domain-first method for designing long-lived software systems. Covers modular monoliths, vertical-slice feature folders, type-driven domain modeling (newtypes, value objects, parse-don't-validate, make-illegal-states-unrepresentable), policies, domain events, explicit consistency models, idempotency, functional-core/imperative-shell, architecture fitness functions, and ADRs. Use this skill whenever the user is designing, scaffolding, structuring, refactoring, or reviewing the architecture of a backend or full-stack system; deciding folder or module layout; weighing abstractions like repositories, CQRS, microservices, or event sourcing; modeling a business domain; or deciding how modules should communicate. Trigger it for questions like "how should I structure this service", "where should this code live", or "is this over-engineered" even when the word architecture is never used. Especially relevant for TypeScript/Node, Rust, and Python services.
---

# Modern Architecture Blueprint

A default approach for building long-lived systems that stay correct, comprehensible, and cheap to change — for both human and AI maintainers. It favors business capabilities over technical layers, locality over abstraction, strong types over runtime checks, and explicit invariants over conventions.

This skill is the decision layer. Use it to pick the *right amount* of architecture for the situation and to know where to look for the detailed pattern. The full catalog lives in `references/`; read the relevant file before applying a pattern in depth.

## How to use this skill

Identify the situation, then act:

- **Designing or scaffolding a new system** → start from the North Star and Core Principles below, lay out modules per `references/structure-and-boundaries.md`, and apply only Stage 1 of the Evolution Path. Do not pre-build later stages.
- **Answering a focused design question** ("repository or not?", "events or a direct call?", "where does this file go?") → use the Decision Rules below and open the one reference file that matches.
- **Reviewing existing code or a design** → walk the Review Checklist near the end of this file, pulling in reference files as needed.
- **Modeling a domain concept** → go to `references/domain-modeling.md`.

The biggest mistake when applying this blueprint is treating its pattern catalog as a checklist to implement up front. It is a menu to pull from on demand. **Every abstraction must earn its existence.**

## North Star

Optimize, in priority order, for:

1. **Correctness** — illegal states are hard or impossible to reach.
2. **Comprehensibility** — a newcomer can follow the business behavior.
3. **Changeability** — features and rules are cheap to evolve.
4. **AI navigability** — an agent can locate and reason about code.
5. **Operational simplicity** — few moving parts to run and observe.

Do **not** optimize for: maximum abstraction, framework independence at all costs, theoretical purity, maximum reuse, or future-proofing requirements that may never arrive.

The rationale: real software work is overwhelmingly adding features, changing business rules, and evolving workflows. It is almost never replacing the database, framework, or transport. Architecture should make the common case cheap, even at the cost of making rare cases (a DB swap) less convenient.

## Core principles

**Optimize for change.** Structure code around what gets modified together, not around hypothetical swaps of infrastructure.

**Locality over layering.** Code that changes together lives together. Prefer feature folders (`orders/refund-order/`) over technical layers (`controllers/`, `services/`, `repositories/`). The primary way to navigate the codebase should be by business behavior, not by technical role.

**Domain first.** Top-level folders are business capabilities (`orders/`, `inventory/`, `shipping/`, `billing/`, `notifications/`), never technical concerns.

**Simplicity until complexity appears.** Do not introduce repositories, factories, CQRS, event sourcing, microservices, or specification hierarchies without a demonstrated, present need.

**Prefer deletion.** Before adding any abstraction, ask: *can this be solved with fewer concepts?* The best abstraction is often the one never introduced.

## The Evolution Path — the central decision tool

Systems should grow through these stages. Stay at the earliest stage that meets current needs. Move to the next stage only when a concrete pain or requirement justifies it — never preemptively.

1. **Stage 1 — Foundation:** Modules + **vertical slices** (use-case/feature folders) + newtypes for identity + parse-don't-validate at the boundary. Each slice holds its own handler and logic. *Almost every project starts and stays here for a long time.*
2. **Stage 2 — Concepts with rules:** Add value objects (Money, Email, Quantity…) for rule-bearing concepts and shared decision logic (see "policies" below) as business rules accumulate and slices start duplicating them. Keep type-driven modeling on throughout — typed states that make illegal states unrepresentable are not an escalation; they belong from the start.
3. **Stage 3 — Rich behavior (escalation, not a default step):** Move behavior onto domain objects (`order.approve()` not `order.status = "Approved"`) and introduce domain events between modules — but only when a concrete trigger appears (see the vertical-slice decision rule below). Vertical slices remain the default home for logic; rich objects are pulled in for specific entities that earn them.
4. **Stage 4 — Enforcement:** Add executable architecture fitness functions and stronger module isolation once boundaries matter enough to police automatically.
5. **Stage 5 — Service extraction:** Split a module into a separate service *only* when operational reality (independent scaling, team ownership, deployment isolation) demands it. Microservices are an optimization, not a starting point.

When unsure which stage a request implies, default to the lower stage and say why. **This blueprint prioritizes vertical slices over rich domain objects** — keep logic in the slice plus a functional core, and centralize behavior on an object only when the triggers below fire.

## Decision rules (quick answers)

**Direct call vs. domain event** — Use a **direct call** when the work is in the same transaction, guards the same invariant, or needs immediate consistency. Use an **event** when another module merely reacts, eventual consistency is acceptable, and you want to reduce coupling. See `references/events-and-consistency.md`.

**Repository or direct ORM?** — Calling the ORM or query builder directly (`orm.orders.create(...)`) is the default and is acceptable. Introduce a repository only when it delivers measurable value (e.g., complex query reuse, a genuine need to abstract a storage swap that is actually planned). Persistence is infrastructure and belongs at the edges.

**Primitive vs. value object / newtype?** — If two values of the same primitive type could be swapped by mistake (two `string` ids), use a newtype. If a concept carries validation, invariants, or behavior (money, email, percentage), use a value object. See `references/domain-modeling.md`.

**Policy or specification?** — Make a **policy** the default home for a business decision: it bundles the related decisions and calculations for one area (`refundPolicy.canRefund(order)`, `refundPolicy.refundAmount(order)`) and reads clearly to humans and AI. Reach for a **specification** (a composable `isSatisfiedBy` predicate) only when you actually compose predicates or drive queries with them — expect on the order of 10–20 policies per specification in a typical business system. Otherwise a method or function (`customer.isEligible()`) beats a specification object. The `policies/` folder is not mandatory; it emerges only when decision logic is shared by 2+ slices. See `references/domain-modeling.md`.

**Vertical slice or rich domain object?** — Default to keeping logic in the **feature slice** plus a functional core (pure functions on typed data). Move behavior onto a domain object (`order.cancel()` rather than mutating `status` in the slice) only when a concrete trigger fires: (a) many related business rules cluster on one entity; (b) an invariant must hold across multiple operations; (c) the entity has a real lifecycle/state machine with illegal transitions to forbid; (d) the same invariant is already enforced from 2+ slices (centralize so it can't drift); or (e) the cost of a violated invariant is high (money, inventory, compliance). Absent a trigger, a rich object is over-engineering. Note: deferring rich objects does **not** defer type-driven modeling — keep illegal states unrepresentable via typed unions regardless.

**One file or a feature folder?** — A small feature may start as `refundOrder.ts` and grow into a `refund-order/` folder (handler, schema, events, tests, README) when it earns the structure. Don't pre-split.

## Pattern map → where to read

| You are working on… | Read |
| --- | --- |
| Folder/module layout, module public APIs, dependency direction, READMEs | `references/structure-and-boundaries.md` |
| Newtypes, value objects, parse-don't-validate, illegal states, policies, rich domain objects, functional core, temporal modeling, idempotency, persistence | `references/domain-modeling.md` |
| Domain events, event naming, direct-call vs event, consistency model, observability | `references/events-and-consistency.md` |
| Unit/integration/acceptance tests, test colocation, fitness functions, ADRs, AI context files | `references/testing-and-governance.md` |

## Naming

Code must speak the business language. Prefer intent-revealing names: `approveOrder()`, `reserveInventory()`, `calculateShippingCost()`. Avoid vague verbs — `process()`, `execute()`, `run()`, `handle()` — unless the intent is immediately obvious from context. Events name business facts in the past tense (`OrderApproved`, `InventoryReserved`), never vague mutations (`OrderUpdated`, `EntityChanged`).

## Final guiding principles

Model the business explicitly. Keep related code together. Use newtypes for identity and value objects for concepts with rules. Parse once at the boundary so everything inside is already valid. Make illegal states unrepresentable. Protect invariants through behavior. Communicate across modules with events when coupling should drop. Enforce architecture with code, not just docs. Record decisions in ADRs. Optimize equally for humans and AI agents. Introduce complexity only when reality demands it.

## Avoid by default

Treat these as smells unless a present, demonstrated need justifies them: microservices first, repositories everywhere, CQRS everywhere, event sourcing everywhere, layer-based folder structures, factory proliferation, specification proliferation, and framework-centric architecture.

## Review checklist

When reviewing a system or design against this blueprint, check:

1. **Organization** — Are top-level folders business capabilities, not technical layers? Are features organized as vertical slices? Does code that changes together live together?
2. **Boundaries** — Does each module expose a narrow public API (`orders/api`)? Do other modules avoid reaching into internals? Is the dependency direction explicit and acyclic?
3. **Types** — Are identities newtypes? Are rule-bearing concepts value objects? Do these live under `domain/` rather than technical-kind folders? Is validation done once at the boundary (parse-don't-validate)? Are illegal states unrepresentable via typed unions?
4. **Behavior** — Is logic in the slice plus a functional core by default, with behavior centralized on a domain object only where a trigger (clustered/cross-operation/duplicated/high-cost invariant, or a real lifecycle) justifies it? Conversely, are there rich objects that *haven't* earned their existence? Is shared decision logic (`policies/`) genuinely shared by 2+ slices, named by intent, and kept distinct from reactive when-then processes?
5. **Communication & consistency** — Is each interaction's consistency requirement explicit? Are events business facts in past tense? Are externally triggered commands idempotent?
6. **Time** — Are temporal facts modeled explicitly (`approvedAt`, `shippedAt`) where business rules depend on them, rather than inferred from a single `status`?
7. **Governance** — Are architectural rules enforced by fitness functions, not only documentation? Do important workflows emit observable, correlated events? Are key decisions captured in ADRs? Is there an `AGENTS.md`/`ARCHITECTURE.md` for humans and agents? Are unit/integration tests colocated, with only e2e/architecture/performance centralized?
8. **Restraint** — Is any abstraction present that has not earned its existence (premature repositories, specification objects, rich domain objects, CQRS)? Could the design be expressed with fewer concepts?

Flag over-engineering as readily as under-engineering. Recommend the lowest Evolution Path stage that satisfies the actual requirements, and name the concrete trigger that would justify moving up.

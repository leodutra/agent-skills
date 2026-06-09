# Structure & Boundaries

How to physically organize a system, expose module APIs, and control dependencies. Read this when laying out a new system or judging an existing layout.

## Architectural style: modular monolith

Default to a **modular monolith**: one deployable, one codebase, with explicit internal module boundaries and internal event communication. Modules evolve independently inside the single deployable.

```text
Application
├── Orders
├── Inventory
├── Shipping
├── Billing
└── Notifications
```

Microservices are an optimization adopted later (Evolution Path Stage 5), not a starting point. Start as a monolith and extract a service only when operational reality (independent scaling, deployment isolation, team ownership) demands it.

## Top-level structure

Organize the top level by **business capability**, with a single shared area and a centralized test area for cross-cutting tests only.

```text
src/
├── orders/
├── inventory/
├── shipping/
├── billing/
├── notifications/
├── shared/
└── tests/
    ├── e2e/
    ├── architecture/
    └── performance/
```

`shared/` holds genuinely cross-cutting code only. Resist the urge to dump anything reusable here; most "shared" code actually belongs to one capability.

## Module structure

Inside a module, organize by **vertical slices** — use-case (feature) folders are the primary unit. Domain primitives live together under `domain/`; shared cross-slice decisions live under `policies/`.

```text
orders/
├── api/                 # the only entry point other modules may import
├── domain/              # business concepts, invariants, newtypes, value objects
├── policies/            # decision logic SHARED by 2+ slices (optional)
├── create-order/        # vertical slices (feature folders) — the primary unit
├── cancel-order/
├── refund-order/
├── approve-order/
└── README.md
```

**Newtypes and value objects live in `domain/`**, not in separate top-level folders. A `CustomerId`, the `Customer` concept, and `Money` are all domain primitives — splitting them into `newtypes/` and `value-objects/` folders organizes by technical kind, which is the layering this blueprint avoids. Keep them colocated with the concept they serve (or as `domain/types.ts`, `domain/value-objects.ts`), and break out dedicated subfolders only when sheer volume makes `domain/` hard to scan.

`domain/` and `policies/` appear as the system reaches the relevant Evolution Path stages. A young module may contain only `api/` and a few slice folders. **Logic defaults to the slice that uses it** — a decision only graduates to `policies/` or behavior only graduates onto a `domain/` object when the triggers in the SKILL.md decision rules fire.

## Feature organization

Features represent use cases. A mature feature is a folder:

```text
refund-order/
├── handler.ts
├── schema.ts
├── events.ts
├── handler.test.ts
└── README.md
```

A small feature may begin life as a single file (`refundOrder.ts`) and grow into a folder when it earns the structure. Do not pre-split a one-function feature into five files.

## Command / query separation

Keep commands and queries conceptually distinct:

- **Commands** change state: `createOrder()`, `cancelOrder()`, `refundOrder()`, `approveOrder()`.
- **Queries** read state: `getOrder()`, `searchOrders()`, `listCustomerOrders()`.

This is a *conceptual* distinction for clarity. It does **not** require CQRS (separate read/write models, separate stores). Adopt CQRS only with demonstrated need.

## Module public API

Every module exposes a narrow public API. Other modules may depend **only** on that surface.

```text
orders/
└── api/
    ├── createOrder.ts
    ├── refundOrder.ts
    └── getOrder.ts
```

Allowed: importing `orders/api`. Forbidden: importing `orders/domain`, `orders/policies`, or any other internal path. The public API is what preserves encapsulation — internals stay free to change as long as the API holds.

## Module README

Every module carries a `README.md` describing:

- **Purpose** — the business capability it owns.
- **Public API** — the entry points other modules may call.
- **Domain concepts** — the key nouns and their meaning (ubiquitous language).
- **Published events** — facts this module emits.
- **Consumed events** — facts this module reacts to.
- **Dependencies** — which other modules it may call, and why.
- **Consistency model** — which interactions are strong vs. eventual.

This README serves humans onboarding *and* AI agents navigating the system. Keep it current; a stale README misleads both.

## Dependency direction

Every module has explicit, intentional, documented dependency rules. Dependencies flow one way and must be acyclic.

```text
Orders → Inventory
Orders → Billing
Shipping ✕ Orders        (forbidden)
```

Document the intended direction (in module READMEs and an ADR) and, once boundaries matter enough, enforce it with architecture fitness functions (see `testing-and-governance.md`). Never rely on documentation alone to keep dependencies honest — humans and agents will violate undocumented-but-unenforced rules.

## Strategic DDD only

Adopt Domain-Driven Design *strategically*: bounded contexts, ubiquitous language, clear domain ownership, explicit business concepts. Do **not** import the full tactical-DDD pattern zoo (aggregates-everywhere, repositories-everywhere, factories, specifications) by default. Pull a tactical pattern in only when a specific problem calls for it.

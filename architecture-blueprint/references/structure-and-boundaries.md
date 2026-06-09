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

Top-level folders MUST be **business capabilities**. The ONLY sanctioned non-capability top-level entries are `shared/` and `tests/`.

```text
src/
├── orders/
├── inventory/
├── shipping/
├── billing/
├── notifications/
├── shared/
└── tests/
    ├── acceptance/
    ├── architecture/
    ├── e2e/
    └── performance/
```

`tests/` holds ONLY cross-module/system tests, in exactly these four canonical buckets (see `testing-and-governance.md`); single-module tests are colocated, and you MUST NOT invent other top-level test folders.

`shared/` MUST contain ONLY genuinely cross-cutting, business-free code (e.g., logging, clock, id generation, error types). Business logic, domain types, and decisions MUST NOT live in `shared/`. When in doubt, code SHOULD belong to a capability, not `shared/` — `shared/` is not an escape hatch. If something in `shared/` acquires business meaning, it MUST move into the owning capability.

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

Allowed: import `orders/api`. Forbidden: importing `orders/domain`, `orders/policies`, or any internal path — other modules MUST NOT do this. The public API preserves encapsulation; internals stay free to change.

## Module README

Each module MUST carry a `README.md` covering: purpose, public API, domain concepts (ubiquitous language), published events, consumed events, dependencies (and why), consistency model. It serves humans and AI agents and MUST be kept current.

## Dependency direction

Dependencies MUST be explicit, one-way, and acyclic.

```text
Orders → Inventory
Orders → Billing
Shipping ✕ Orders        (forbidden)
```

Document direction (READMEs + ADR). Once boundaries matter, you MUST enforce it with architecture fitness functions (see `testing-and-governance.md`); documentation alone CANNOT hold, because unenforced rules erode and agents cross any boundary nothing stops.

## Strategic DDD only

Use bounded contexts, ubiquitous language, domain ownership, explicit business concepts. You MUST NOT import the tactical-DDD pattern zoo (aggregates/repositories/factories/specifications everywhere) by default; pull a pattern in ONLY when a specific problem calls for it.

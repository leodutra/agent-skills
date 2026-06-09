# Structure & Boundaries

Physical organization, module APIs, dependency control.

## Modular monolith (default)

One deployable, one codebase, explicit internal module boundaries, internal event communication. Modules evolve independently inside it.

```text
Application
├── Orders
├── Inventory
├── Shipping
├── Billing
└── Notifications
```

Microservices come later (Evolution Path Stage 5), only when operational reality (scaling, deployment isolation, team ownership) demands extraction.

## Top-level structure

By **business capability**, plus one `shared/` area and a central test area for cross-cutting tests only.

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

`shared/` is for genuinely cross-cutting code only; most "shared" code belongs to one capability.

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

**Newtypes and value objects live in `domain/`**, not in separate `newtypes/`/`value-objects/` folders (that organizes by technical kind — the layering this blueprint avoids). Break out subfolders only when volume makes `domain/` hard to scan. `domain/` and `policies/` appear as stages are reached; a young module may have only `api/` and slice folders. **Logic defaults to the slice that uses it** — it graduates to `policies/` or onto a `domain/` object only when the SKILL.md triggers fire.

## Feature organization

A mature feature is a folder; a small one starts as a single file and grows when it earns it. Don't pre-split a one-function feature.

```text
refund-order/
├── handler
├── schema
├── events
├── handler.test
└── README
```

## Command / query separation

Conceptual distinction only: **commands** change state (`createOrder()`, `refundOrder()`); **queries** read state (`getOrder()`, `searchOrders()`). Does **not** require CQRS (separate models/stores) — adopt that only with demonstrated need.

## Module public API

Each module exposes a narrow public API; others depend **only** on it.

```text
orders/
└── api/
    ├── createOrder
    ├── refundOrder
    └── getOrder
```

Allowed: import `orders/api`. Forbidden: import `orders/domain`, `orders/policies`, or any internal path. The API preserves encapsulation; internals stay free to change.

## Module README

Each module's `README.md` covers: purpose, public API, domain concepts (ubiquitous language), published events, consumed events, dependencies (and why), consistency model. Serves humans and AI agents; keep it current.

## Dependency direction

Explicit, documented, one-way, acyclic.

```text
Orders → Inventory
Orders → Billing
Shipping ✕ Orders        (forbidden)
```

Document direction (READMEs + ADR) and enforce with architecture fitness functions (see `testing-and-governance.md`) once boundaries matter. Documentation alone won't hold — humans and agents violate unenforced rules.

## Strategic DDD only

Use bounded contexts, ubiquitous language, domain ownership, explicit business concepts. Do **not** import the tactical-DDD pattern zoo (aggregates/repositories/factories/specifications everywhere) by default — pull a pattern in only when a specific problem calls for it.

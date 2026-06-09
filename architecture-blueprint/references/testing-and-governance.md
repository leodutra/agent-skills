# Testing & Governance

Test strategy and placement, executable architecture rules, decision records, AI alignment. (Keyword conventions: see SKILL.md.)

## Testing strategy (by focus)

- **Unit** — pure, rule-bearing pieces: newtypes, value objects, policies (incl. `can*` authorization), domain objects, functional core. Most correctness guarantees live here.
- **Integration** — a **single module's** infrastructure seams: its persistence, its event handling. Single-module scope.
- **Acceptance** — business behavior in business language ("Given a delivered order, when a refund is requested within 30 days, then it is approved"). MAY be single-slice (one use case) or cross-module (a flow/lifecycle).
- **E2E** — the whole system through real infrastructure (API → DB → bus → worker).

A cross-module business flow (e.g., create → approve → invoice) is an **acceptance** test, NOT integration (which is single-module) and NOT e2e (which goes through the real stack). Use this to place it.

## Test placement (by scope)

Dividing rule (by **scope/ownership**, not by test type): a test that owns a **single** module/slice — unit, integration, OR acceptance — SHOULD be colocated with it; a test whose behavior spans **multiple** modules MUST live in `tests/`. Colocation maximizes cohesion — tests evolve and move with their code (safe refactors, no orphaned test tree) and stay discoverable.

So a single-module integration test (one module's persistence) is **colocated**, not centralized; only cross-module behavior is centralized.

**Colocate (single-module):** a sibling test file or an in-module test block.

> Rust: a sibling `tests.rs`, or in-file `#[cfg(test)] mod tests { ... }` — the in-file form can test private and `pub(crate)` items without exposing them.

```text
orders/
├── approve-order/
│   ├── handler
│   ├── policy            # can_approve_order
│   └── tests             # colocated, owns this slice
└── domain/
    ├── order
    └── tests
```

**Centralize in `tests/` (multi-module / system).** This tree is **canonical** — you MUST use these four buckets and MUST NOT invent ad-hoc top-level test folders. Cross-module acceptance flows go under `tests/acceptance/`, not loose files.

```text
tests/
├── acceptance/           # cross-module business flows (e.g., create -> approve -> invoice)
├── architecture/         # fitness functions (Rust: here or in xtask/)
├── e2e/                  # API -> DB -> bus -> worker
└── performance/          # load / latency / throughput
```

A test that spans modules is a system concern, not a module concern, and MUST NOT be placed inside any one module.

## Architecture fitness functions

Architectural rules MUST be **executable** and MUST fail the build when violated.

```text
Orders must not depend on Shipping
Domain must not depend on infrastructure
```

Enforce via static analysis, dependency-constraint checks, or import-graph assertions; place them in `tests/architecture/` (Rust: there or `xtask/`). Documentation alone CANNOT hold — unenforced rules erode and agents cross any boundary nothing stops. Introduce at Evolution Path Stage 4.

## ADRs

Significant decisions MUST be recorded as ADRs; they are the authoritative record of intent.

**Agent directive:** whenever you conclude a considerable architectural decision or definition — choosing a module boundary, a consistency model, an event vs. direct call, a persistence approach, escalating to a rich domain object, adopting a pattern, etc. — you MUST record it as an ADR (or, if unsure it clears that bar, explicitly propose one to the user). You MUST keep ADRs maintained: when a later decision changes an earlier one, mark the old ADR **Superseded** (linking the replacement) rather than editing away the history, and keep the index current. Stale or missing ADRs are a defect.

```text
docs/adr/
├── 001-architecture.md
├── 002-module-boundaries.md
├── 003-domain-events.md
├── 004-testing-strategy.md
└── 005-persistence.md
```

Each ADR MUST contain: **Context** (forces/constraints), **Decision** (what was chosen), **Consequences** (what it eases and what it costs), and **Status** (Proposed / Accepted / Superseded). Capturing the "why" stops future maintainers and agents from re-learning old lessons.

## AI context file

Maintain `AGENTS.md` (or `ARCHITECTURE.md`) covering: architecture summary + North Star, module boundaries, naming rules, architectural constraints (what fitness functions enforce), ADR references, development conventions. It keeps humans and agents on the same model; without it, agents guess and drift.

# Testing & Governance

Test strategy and placement, executable architecture rules, decision records, AI alignment. (Keyword conventions: see SKILL.md.)

## Testing strategy (by focus)

- **Unit** — pure, rule-bearing pieces: newtypes, value objects, policies (incl. `can*` authorization), domain objects, functional core. Most correctness guarantees live here.
- **Integration** — a **single module's** infrastructure seams: its persistence, its event handling. Single-module scope.
- **Acceptance** — business behavior in business language ("Given a delivered order, when a refund is requested within 30 days, then it is approved"). MAY be single-slice (one use case) or cross-module (a flow/lifecycle).
- **E2E** — the whole system through real infrastructure (API → DB → bus → worker).

A cross-module business flow (e.g., create → approve → invoice) is an **acceptance** test, NOT integration and NOT e2e.

## Test placement (by scope)

Dividing rule (by **scope/ownership**, not by test type): a test that owns a **single** module/slice — unit, integration, OR acceptance — SHOULD be colocated with it; a test whose behavior spans **multiple** modules MUST live in `tests/`.

A single-module integration test is **colocated**, not centralized.

**Colocate (single-module):** a sibling test file or an in-module test block.

> Rust: use a sibling `tests.rs` or in-file `#[cfg(test)] mod tests { ... }`.

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
├── architecture/         # fitness functions (Rust: repo-level xtask/ MAY invoke these)
├── e2e/                  # API -> DB -> bus -> worker
└── performance/          # load / latency / throughput
```

A test that spans modules MUST NOT be placed inside any one module.

## Architecture fitness functions

Architectural rules MUST be **executable** and MUST fail the build when violated.

```text
Orders must not depend on Shipping
Domain must not depend on infrastructure
```

Enforce via static analysis, dependency-constraint checks, or import-graph assertions; place them in `tests/architecture/`. In Rust repositories, a repo-level `xtask/` MAY orchestrate or invoke those checks, but it does not replace the canonical `tests/architecture/` bucket. Documentation alone CANNOT enforce boundaries. Introduce at Evolution Path Stage 4.

## ADRs

Significant decisions MUST be recorded as ADRs.

**Agent directive:** when you conclude a considerable architectural decision or definition, you MUST record it as an ADR or explicitly propose one. When a later decision changes an earlier one, you MUST mark the old ADR **Superseded** and link the replacement. Stale or missing ADRs are a defect.

```text
docs/adr/
├── 001-architecture.md
├── 002-module-boundaries.md
├── 003-domain-events.md
├── 004-testing-strategy.md
└── 005-persistence.md
```

Each ADR MUST contain: **Context** (forces/constraints), **Decision** (what was chosen), **Consequences** (what it eases and what it costs), and **Status** (Proposed / Accepted / Superseded).

## AI context file

Maintain `AGENTS.md` (or `ARCHITECTURE.md`) covering: architecture summary + North Star, module boundaries, naming rules, architectural constraints (what fitness functions enforce), ADR references, development conventions.

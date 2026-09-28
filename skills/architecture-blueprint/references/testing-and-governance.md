# Testing & Governance

Test strategy and placement, executable architecture rules, decision records, AI alignment. (Keywords and the `(n)` / `(frame)` / `(ledger)` tags: see SKILL.md.)

The currency ladder (`first-principles.md`, §The frame) organizes this file. Types pay obligations at rung 1 — by the machine, at construction, once. Tests and fitness functions are rung 2: the mechanized ledger of obligations structure could not absorb, re-audited at every change. ADRs, READMEs, and `AGENTS.md` are rung 3: one author, once, recorded — testimony (3) that binds only its reader. Nothing in this file is meant to sit at rung 4, and anything that does — a rule everyone "just knows" — is a defect to move up the ladder.

## Testing strategy (by focus)

(frame, rung 2; 4 — a case that cannot be constructed needs no test) Test what the types could not hold. A property the type system already enforces needs no test; a property it cannot express — a business rule, an algebraic law, a boundary assumption — is exactly what the suite exists to hold.

- **Unit** — pure, rule-bearing pieces: newtypes, value objects, policies, authorization decisions (`can` → `Permit`), domain objects, functional core. This is where the rules the types cannot hold are checked. A slice's handler exercised with doubles at its capability seams is a unit test too; the double SHOULD be a fake implementing the capability (an in-memory store), not a mock scripting calls (5 — an interface states capability, not machinery, and a mock couples the test to the machinery).
- **Property-based** (ledger; 10) — laws stated over a space of inputs, not a sample: idempotence (`f(f(x)) = f(x)`), commutativity and associativity of merges, round-trips (`parse(serialize(x)) = x`), value-object invariants. SHOULD be used wherever a law of principle 10 is relied upon: an example-based test of a law binds only the cases it states.
- **Integration** — a **single module's** infrastructure seams against real infrastructure: its persistence against the real database, its event handling against the real bus. Single-module scope.
- **Contract** (ledger; 14, 2) — mechanically checkable boundary assumptions: the shape and semantics a module's `api/` and published events promise, checked from the consumer's side, so a chain of modules can be trusted from contracts alone.
- **Acceptance** — business behavior in business language ("Given a delivered order, when a refund is requested within 30 days, then it is approved"). MAY be single-slice (one use case) or cross-module (a flow/lifecycle).
- **E2E** — the whole system through real infrastructure (API → DB → bus → worker).

A cross-module business flow (e.g., create → approve → invoice) is an **acceptance** test, NOT integration and NOT e2e.

## Test placement (by scope)

(14 — what is needed to verify a thing should live near the thing) Dividing rule (by **scope/ownership**, not by test type): a test that owns a **single** module/slice — unit, integration, OR acceptance — SHOULD be colocated with it; a test whose behavior spans **multiple** modules MUST live in `tests/`, never inside any one module.

**Colocate (single-module)** — a single-module integration test included: a sibling test file or an in-module test block (Rust: a sibling `tests.rs` or in-file `#[cfg(test)] mod tests { ... }`).

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

**Centralize in `tests/` (multi-module / system).** This tree is **canonical** (*convention*) — you MUST use these four buckets and MUST NOT invent ad-hoc top-level test folders. Cross-module acceptance flows go under `tests/acceptance/`, not loose files.

```text
tests/
├── acceptance/           # cross-module business flows (e.g., create -> approve -> invoice)
├── architecture/         # fitness functions no linter configuration can express
├── e2e/                  # API -> DB -> bus -> worker
└── performance/          # load / latency / throughput
```

## Architecture fitness functions

(3 — constraints by construction beat conventions by discipline; frame, rung 2) Introduce at Evolution Path Stage 4, when boundaries need policing. Once introduced, architectural rules MUST be **executable** and MUST fail the build when violated.

```text
Orders must not depend on Shipping
Domain must not depend on infrastructure
```

**Existing linters, configured — never a custom checker** (frame; 13). A fitness function SHOULD be a rule in a linter the project already runs, or in one established tool per concern, whose configuration states the architectural rule. You MUST NOT build a custom checker (a home-grown script, AST walker, or bespoke build task) for a rule an existing tool can express: the checker is a second codebase with obligations of its own, paid at every change. Where structure can hold a rule, it comes first (rung 1): internals the language makes private cannot be reached around `api/`. Only an assertion no linter configuration can express is written as a test in `tests/architecture/`. Documentation alone CANNOT enforce boundaries (3 — a README is testimony).

Candidates — each a rule of this skill the type system cannot hold — and the existing tool that holds it:

| Rule | TypeScript | Python | Rust |
| --- | --- | --- | --- |
| Other modules import only a module's `api/` (5) | `import/no-restricted-paths` (eslint-plugin-import), or dependency-cruiser | import-linter `forbidden` contract | the compiler: internals private, only `api` public |
| Dependencies one-way and acyclic (5) | `import/no-cycle`, or dependency-cruiser | import-linter `layers` contract | the compiler, with a crate per module |
| `domain/` imports no infrastructure or framework (7, 8) | `no-restricted-imports`, scoped to `domain/` | import-linter `forbidden` contract | the domain crate does not depend on them |
| Validation libraries and `env` read only in boundary files and the composition root (7, 8) | `no-restricted-imports` and `no-restricted-properties` (`process.env`), off for those files | ruff `TID251` (banned-api), with `per-file-ignores` for those files | clippy `disallowed-methods` (`std::env::var`), expected in those files |
| No clock or randomness outside the imperative shell and `platform/` (7) | `no-restricted-properties` (`Date.now`, `Math.random`) and `no-restricted-syntax` (`new Date()`) | ruff `TID251` in the core folders' own `ruff.toml` | clippy `disallowed-methods` in the core crate's `clippy.toml` |
| No primitive where a newtype exists, no newtype unwrapped outside boundary files (1) | review | review | review |

## ADRs

(13 — design decisions are themselves framed facts; 2 — rules are part of the frame; rung 3) Significant decisions MUST be recorded as ADRs. A decision that lives only in the deciders' memory sits at rung 4 and reverts to *unknown* for every later maintainer (1, A2).

**Agent directive:** when you conclude a considerable architectural decision or definition, you MUST record it as an ADR or explicitly propose one. When a later decision changes an earlier one, you MUST mark the old ADR **Superseded** and link the replacement — the earlier decision's frame has expired, and the record MUST say so. Stale or missing ADRs are a defect.

```text
specs/adr/
├── 001-architecture.md
├── 002-module-boundaries.md
├── 003-domain-events.md
├── 004-testing-strategy.md
└── 005-persistence.md
```

Each ADR MUST contain (*convention* on the sections): **Context** (forces/constraints), **Decision** (what was chosen), **Consequences** (what it eases and what it costs — stated as obligations: which the decision discharges, which it creates, and who pays them in what currency; §The tests, questions 1–3), and **Status** (Proposed / Accepted / Superseded).

## AI context file

(A1 — the machine maintainer is a bounded reasoner too; 14; rung 3) Maintain `AGENTS.md` (or `ARCHITECTURE.md`) covering: architecture summary + North Star, module boundaries, naming rules, architectural constraints (what fitness functions enforce), ADR references, development conventions. It is testimony: keep it true, and keep every rule it states that structure could hold instead moving up the ladder.

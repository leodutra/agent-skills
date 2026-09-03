# Testing & Governance

Test strategy and placement, executable architecture rules, decision records, AI alignment. (Keyword conventions: see SKILL.md. Tags `(n)` name the deriving principle in `first-principles.md`; `(ledger)` its pattern-ledger entry.)

The currency ladder (`first-principles.md`, §The frame) organizes this file. Types pay obligations at rung 1 — by the machine, at construction, once. Tests and fitness functions are rung 2: the mechanized ledger of obligations structure could not absorb, re-audited at every change. ADRs, READMEs, and `AGENTS.md` are rung 3: one author, once, recorded — testimony (3) that binds only its reader. Nothing in this file is meant to sit at rung 4, and anything that does — a rule everyone "just knows" — is a defect to move up the ladder.

## Testing strategy (by focus)

(frame, rung 2; 4 — a case that cannot be constructed needs no test) Test what the types could not hold. A property the type system already enforces needs no test; a property it cannot express — a business rule, an algebraic law, a boundary assumption — is exactly what the suite exists to hold.

- **Unit** — pure, rule-bearing pieces: newtypes, value objects, policies (incl. `can*` authorization), domain objects, functional core. This is where the rules the types cannot hold are checked. A slice's handler exercised with doubles at its capability seams is a unit test too; the double SHOULD be a fake implementing the capability (an in-memory store), not a mock scripting calls (5 — an interface states capability, not machinery, and a mock couples the test to the machinery).
- **Property-based** (ledger; 10) — laws stated over a space of inputs, not a sample: idempotence (`f(f(x)) = f(x)`), commutativity and associativity of merges, round-trips (`parse(serialize(x)) = x`), value-object invariants. SHOULD be used wherever a law of principle 10 is relied upon: an example-based test of a law binds only the cases it states.
- **Integration** — a **single module's** infrastructure seams against real infrastructure: its persistence against the real database, its event handling against the real bus. Single-module scope.
- **Contract** (ledger; 14, 2) — mechanically checkable boundary assumptions: the shape and semantics a module's `api/` and published events promise, checked from the consumer's side, so a chain of modules can be trusted from contracts alone.
- **Acceptance** — business behavior in business language ("Given a delivered order, when a refund is requested within 30 days, then it is approved"). MAY be single-slice (one use case) or cross-module (a flow/lifecycle).
- **E2E** — the whole system through real infrastructure (API → DB → bus → worker).

A cross-module business flow (e.g., create → approve → invoice) is an **acceptance** test, NOT integration and NOT e2e.

## Test placement (by scope)

(14 — what is needed to verify a thing should live near the thing) Dividing rule (by **scope/ownership**, not by test type): a test that owns a **single** module/slice — unit, integration, OR acceptance — SHOULD be colocated with it; a test whose behavior spans **multiple** modules MUST live in `tests/`.

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

**Centralize in `tests/` (multi-module / system).** This tree is **canonical** (*convention*) — you MUST use these four buckets and MUST NOT invent ad-hoc top-level test folders. Cross-module acceptance flows go under `tests/acceptance/`, not loose files.

```text
tests/
├── acceptance/           # cross-module business flows (e.g., create -> approve -> invoice)
├── architecture/         # fitness functions (Rust: repo-level xtask/ MAY invoke these)
├── e2e/                  # API -> DB -> bus -> worker
└── performance/          # load / latency / throughput
```

A test that spans modules MUST NOT be placed inside any one module.

## Architecture fitness functions

(3 — constraints by construction beat conventions by discipline; frame, rung 2) Introduce at Evolution Path Stage 4, when boundaries need policing. Once introduced, architectural rules MUST be **executable** and MUST fail the build when violated.

```text
Orders must not depend on Shipping
Domain must not depend on infrastructure
```

Enforce via static analysis, dependency-constraint checks, or import-graph assertions; place them in `tests/architecture/`. In Rust repositories, a repo-level `xtask/` MAY orchestrate or invoke those checks, but it does not replace the canonical `tests/architecture/` bucket. Documentation alone CANNOT enforce boundaries (3 — a README is testimony).

Candidates beyond dependency direction — each a rule of this skill that the type system cannot hold and that a mechanized check can:

- no import of another module's internals — only its `api/` (5);
- no `domain/` import of infrastructure or frameworks (7, 8);
- no primitive `string`/`number` in slice entry signatures where a newtype exists, and no newtype unwrapped outside boundary files — parse-don't-validate and no-decay proxies (1);
- no validation-library import, and no `env`/`process.env`/`os.environ` access, outside boundary files and the composition root (7, 8);
- no `Date.now()`/`new Date()`/`SystemTime::now()`/`random` outside the imperative shell and `platform/` (7).

## ADRs

(13 — design decisions are themselves framed facts; 2 — rules are part of the frame; rung 3) Significant decisions MUST be recorded as ADRs. A decision that lives only in the deciders' memory sits at rung 4 and reverts to *unknown* for every later maintainer (1, A2).

**Agent directive:** when you conclude a considerable architectural decision or definition, you MUST record it as an ADR or explicitly propose one. When a later decision changes an earlier one, you MUST mark the old ADR **Superseded** and link the replacement — the earlier decision's frame has expired, and the record MUST say so. Stale or missing ADRs are a defect.

```text
docs/adr/
├── 001-architecture.md
├── 002-module-boundaries.md
├── 003-domain-events.md
├── 004-testing-strategy.md
└── 005-persistence.md
```

Each ADR MUST contain (*convention* on the sections): **Context** (forces/constraints), **Decision** (what was chosen), **Consequences** (what it eases and what it costs — stated as obligations: which the decision discharges, which it creates, and who pays them in what currency; §The tests, questions 1–3), and **Status** (Proposed / Accepted / Superseded).

## AI context file

(A1 — the machine maintainer is a bounded reasoner too; 14; rung 3) Maintain `AGENTS.md` (or `ARCHITECTURE.md`) covering: architecture summary + North Star, module boundaries, naming rules, architectural constraints (what fitness functions enforce), ADR references, development conventions. It is testimony: keep it true, and keep every rule it states that structure could hold instead moving up the ladder.

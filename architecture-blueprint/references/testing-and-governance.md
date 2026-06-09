# Testing & Governance

Test strategy, executable architecture rules, decision records, AI alignment.

## Testing strategy

- **Unit** — pure, rule-bearing pieces: newtypes, value objects, policies, domain objects, functional core. Fast and deterministic; most correctness guarantees live here.
- **Integration** — infrastructure seams: persistence, event handling, module interaction. Verify the imperative shell wires the core to the outside correctly.
- **Acceptance** — business behavior in business language: "Given a delivered order, when a refund is requested within 30 days, then it is approved."

## Test colocation

Unit and integration tests live **beside the code they verify** (hard default — they move with the code and stay discoverable). Use the language's idiom: a sibling test file (`Money.<ext>` + `Money.test.<ext>`) or an in-module test block.

Only **cross-cutting** tests are centralized:

```text
tests/
├── e2e/           # whole-system flows
├── architecture/  # fitness functions
└── performance/   # load / latency / throughput
```

## Architecture fitness functions

Architectural rules must be **executable**, failing the build when violated.

```text
Orders must not depend on Shipping
Billing must not depend on Notifications
```

Enforce via static analysis, dependency-constraint checks, or import-graph assertions. Documentation alone won't hold — unenforced rules erode and agents cross any boundary nothing stops. Introduce at Evolution Path Stage 4.

## ADRs

Record significant decisions; they are the authoritative record of intent.

```text
docs/adr/
├── 001-architecture.md
├── 002-module-boundaries.md
├── 003-domain-events.md
├── 004-testing-strategy.md
└── 005-persistence.md
```

Each ADR: **Context** (forces/constraints), **Decision** (what was chosen), **Consequences** (what it eases and what it costs). Captures the "why" so future maintainers and agents don't re-learn old lessons.

## AI context file

Maintain `AGENTS.md` (or `ARCHITECTURE.md`) covering: architecture summary + North Star, module boundaries, naming rules, architectural constraints (what fitness functions enforce), ADR references, development conventions. Keeps humans and agents on the same model; without it, agents guess and drift.

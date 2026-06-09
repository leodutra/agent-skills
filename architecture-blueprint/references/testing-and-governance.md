# Testing & Governance

How to test the system, enforce architecture with executable rules, and record intent so humans and AI agents stay aligned. Read this when setting up a test strategy, policing boundaries, or documenting decisions.

## Testing strategy

Match the test type to what it verifies.

### Unit tests

Focus on the pure, rule-bearing pieces: newtypes, value objects, policies, domain objects, and pure functions (the functional core). These are deterministic and fast, so test them thoroughly — this is where most correctness guarantees should live.

### Integration tests

Focus on the seams that touch infrastructure: persistence, event handling, and module interaction. They verify that the imperative shell wires the core to the outside world correctly.

### Acceptance tests

Focus on business behavior, expressed in business language:

```text
Given a delivered order
When a refund is requested within 30 days
Then the refund is approved
```

Acceptance tests document and verify the rules a stakeholder would recognize.

## Test colocation

Unit and integration tests live **beside the code they verify**. Only genuinely broad, cross-cutting tests (e2e, architecture, performance) get centralized — see below. This is a hard default, not a preference: colocated tests move with their code, stay discoverable, and never rot in a parallel directory tree.

Use whatever colocation idiom the language provides — a sibling test file next to the source, or an in-module test block within it. The example below uses a sibling file:

```text
Money.<ext>
Money.test.<ext>
```

Colocation improves locality, makes navigation obvious, helps AI agents discover the relevant tests, and lowers maintenance cost (move the code, the test comes with it).

## Centralized tests

Only **cross-cutting** tests belong in a central location:

```text
tests/
├── e2e/            # whole-system end-to-end flows
├── architecture/   # fitness functions (see below)
└── performance/    # load / latency / throughput
```

Everything else stays colocated with its module.

## Architecture fitness functions

Architectural rules must be **executable**, not merely documented. Encode each boundary rule as a test that fails the build when violated.

```text
Orders must not depend on Shipping
Billing must not depend on Notifications
```

Enforce via static analysis, dependency-constraint checks, or architecture tests (e.g., tools that assert allowed import graphs). The principle: never rely solely on documentation to keep architecture honest — undocumented-but-unenforced rules erode under deadline pressure, and AI agents will cheerfully cross any boundary that nothing stops them from crossing. A red test is the only reliable guardrail.

Introduce fitness functions at Evolution Path Stage 4 — once boundaries matter enough to be worth policing automatically.

## ADRs — Architecture Decision Records

Record significant decisions as ADRs. They are the authoritative record of architectural intent.

```text
docs/
└── adr/
    ├── 001-architecture.md
    ├── 002-module-boundaries.md
    ├── 003-domain-events.md
    ├── 004-testing-strategy.md
    └── 005-persistence.md
```

Each ADR contains:

- **Context** — the forces and constraints in play.
- **Decision** — what was chosen.
- **Consequences** — what this makes easier and what it makes harder.

ADRs answer the question a future maintainer (or agent) always asks: *why is it this way?* Capturing the "why" prevents well-meaning rewrites that re-learn old lessons the hard way.

## AI context files

Maintain a top-level context file for both human onboarding and AI alignment:

```text
AGENTS.md
```

or:

```text
ARCHITECTURE.md
```

Contents:

- **Architecture summary** — the style and the North Star.
- **Module boundaries** — what each module owns and may depend on.
- **Naming rules** — the business-language conventions.
- **Architectural constraints** — the rules fitness functions enforce.
- **ADR references** — pointers to the decision records.
- **Development conventions** — how work is structured here.

This file keeps humans and AI agents working from the same model of the system. An agent given a clear `AGENTS.md` produces changes consistent with the architecture; an agent without one guesses, and its guesses drift.

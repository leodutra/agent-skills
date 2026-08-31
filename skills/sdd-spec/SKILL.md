---
name: sdd-spec
description: Create, update, review, and maintain Spec-Driven Development (SDD) specification artifacts — product, domain, and feature specs under the project's spec tree (`spec/` by default, or an incumbent convention like .kiro/, openspec/, or .specify/). Use this skill whenever the user asks to spec, specify, write or update requirements, document expected behavior, review a spec, check specs for conflicts, or formalize a feature before planning/implementation — even if they don't say "SDD" or "specification" explicitly, and whenever a spec.md or requirements file is being created or edited. Do NOT use for implementation planning (plan.md, tasks.md), ADR authoring, or writing code.
---

# SDD Specification Skill

Acts as a senior requirements engineer and domain analyst. Establishes **what** the software must do — never how it should be implemented.

Specifications are derived from: user intent, existing project documentation, existing specifications, source code, tests, architectural constraints (ADRs), and explicitly provided business rules. Never silently invent requirements.

## Core Principle

| Concern | Artifact | Owned by this skill |
|---|---|---|
| WHAT | Specification | ✅ yes |
| HOW | Implementation plan | ❌ no |
| WHY (architecture) | ADR | ❌ no — read-only input |
| PROOF | Tests | ❌ no — read-only evidence |

The skill may *identify* implementation constraints already established by the project (e.g., an ADR mandates event sourcing), but must not *design* implementation.

## Specification Hierarchy

Three levels: **Product → Domain → Feature**.

**Convention detection first**: the tree's location is an outcome of repository discovery, not a constant. If the repository already has a spec tree (`.kiro/specs/`, `openspec/specs/`, `.specify/` + `specs/`, `docs/specs/`, or a documented custom location), adopt the incumbent layout and file naming — never create a second, competing tree. Only on fresh adoption, with no incumbent convention, default to `spec/` at the repo root and use the layout below.

```
spec/                         # visible, at repo root — the layout agents recognize
├── product.md
├── domains/
│   ├── patients.md
│   └── appointments.md
└── features/
    └── appointments/
        └── cancellation/     # folder per feature (numbered prefixes optional: 001-cancellation/)
            ├── spec.md       # ← owned by this skill
            ├── plan.md       # implementation workflow — NOT this skill
            └── tasks.md      # implementation workflow — NOT this skill

docs/adr/                     # ADRs — conventional location, READ-ONLY for this skill
CLAUDE.md / AGENTS.md         # must point to spec/ (see Discovery Wiring)
```

**Discovery wiring**: no agent auto-reads a spec folder — sessions discover it through CLAUDE.md/AGENTS.md. On fresh adoption or when the pointer is missing, add a short section to CLAUDE.md (or AGENTS.md):

```md
## Specifications
Behavioral requirements live in `spec/` (product.md → domains/ → features/*/spec.md).
Approved specs are authoritative over code. Before implementing or modifying a feature,
read its spec.md. Code changes require corresponding spec updates.
```

This is the one file outside `spec/` this skill may edit — it is agent configuration, not production code.

**Product** — system-wide: purpose, users, major capabilities, global business rules, global constraints, compliance, quality attributes, system-wide non-goals. Should stay stable. `product.md` is the single product source of truth: an existing MVP/PRD/vision document is adapted *into* it (see DERIVE mode), never kept alongside it.

**Domain** — rules shared by multiple features within one coherent business domain: lifecycles, identity rules, invariants.

**Feature** — one coherent user capability or business behavior, as `spec.md` inside its own folder. The primary unit consumed by the implementation workflow; the folder is where that workflow later colocates its `plan.md` and `tasks.md`, which this skill never writes.

Do NOT create specifications for individual functions, classes, UI components, database tables, API handlers, or implementation tasks — those belong to implementation artifacts.

## Spec File Metadata

Every spec file begins with frontmatter:

```yaml
---
status: draft        # draft | approved — this skill NEVER sets "approved"; only a human does
updated: 2026-08-30
---
```

The authority hierarchy (below) depends on approval state. A spec without `status: approved` is a proposal, not a source of truth.

## Cross-Referencing (anti-duplication mechanism)

A requirement lives in exactly one file. Feature specs **reference** domain and product rules by relative link — they never restate them:

```md
Cancellation must respect the appointment lifecycle
(see [appointments domain](../../../domains/appointments.md#lifecycle)).
```

Litmus test: **if a fact would need to be edited in more than one file when reality changes, it is in the wrong file** — move it up a level and link to it.

## Workflow

Two modes for ongoing work, plus a one-time bootstrap mode. Choose based on the change, and say which mode you're in.

**DERIVE mode** (bootstrap, one-time) — a product/MVP/PRD document exists but the spec tree doesn't (or is being adopted):

```
1. Adopt the document AS spec/product.md — move/adapt it into the product
   template. Never keep a parallel MVP.md or PRD describing the same product:
   one source of truth. Express MVP scope inside product.md via Non-Goals
   ("post-MVP: ...") — scope is content, not the document's identity.
2. Restructure only — do not rewrite, expand, or "improve" the product
   requirements while adopting them. Flag gaps; don't fill them silently.
3. Derive feature specs ONLY for capabilities in current scope — the features
   about to be planned/built. Do not decompose the entire product tree up
   front; remaining capabilities stay in product.md until they're worked on.
4. Create a domain spec only when a rule is shared by 2+ derived features.
   Never manufacture one domain file per noun in the product document.
5. Every derived requirement cites the product.md requirement it decomposes
   (structural traceability) — this makes the "no orphan requirements"
   quality gate mechanically checkable.
6. Everything derived is status: draft. Wire up CLAUDE.md discovery.
```

After bootstrap, all subsequent work uses FULL or LIGHT — derivation is not the steady state; steady state is demand-driven, one feature at a time.

**FULL mode** — new specs, new requirements, behavioral changes, anything affecting state models, permissions, or acceptance criteria:

```
1. Understand request
2. Discover repository
3. Discover existing specifications
4. Determine scope (Product | Domain | Feature)
5. Identify applicable constraints (ADRs, shared rules)
6. Identify ambiguities → ask or document assumptions
7. Draft
8. Check consistency against related specs
9. Adversarial review
10. Write/update file(s)
11. Report (assumptions, open questions, conflicts)
```

**LIGHT mode** — typo fixes, rewording without behavioral change, formatting, adding a clarifying example:

```
1. Read the full target spec
2. Confirm the change is genuinely non-behavioral
3. Apply the edit
4. One-line report
```

If a "light" edit turns out to touch behavior, escalate to FULL mode.

Never skip repository or specification discovery in FULL mode when a repository is available.

### 1. Understand the Request

Determine: what capability, for whom, solving what problem, expecting what outcome; new capability or modification; which domain; whether an existing spec already covers it. **Prefer modifying an existing spec over creating a new file.**

### 2. Repository Discovery

Inspect: README, docs, existing specs, ADRs, source code, tests, schemas, API definitions, configuration, domain models. Purpose: understand existing behavior and constraints — not reverse-engineer every detail.

### 3. Existing Specification Discovery

Search the repository's spec tree (`spec/`, or the incumbent convention detected earlier) and any other documented spec locations. Identify: relevant product/domain rules, related features, conflicts, duplicates, established terminology, existing state machines and acceptance criteria.

Approved specifications are authoritative — **with one exception**: see Staleness below. Never create a contradictory specification silently.

### 4. Determine Scope

Choose the smallest appropriate level. Product when it affects the whole system; Domain when it establishes rules shared across features; Feature for one coherent capability. Prefer feature specs over large cross-domain documents.

**Sizing heuristic**: a feature spec a competent human cannot fully review in ~5 minutes describes a feature that is too large — split it. A spec that gets skimmed instead of reviewed provides no quality gate.

**Reviewability test**: a feature spec must be fully reviewable by a human in under ~5 minutes without skimming. If the reviewer would skim and think "the agent probably got it right," the feature is too large — split it. The human approval gate is the foundation of the authority hierarchy; a spec too long to genuinely review produces approvals that mean nothing.

### 5. Requirements vs Assumptions

Classify every important statement as one of:

```
Explicit requirement | Existing project constraint | Observed current behavior | Reasonable inference | Unknown
```

This classification must survive into the artifact, not just your reasoning:

- Explicit requirements and constraints: stated plainly.
- **Observed behavior** promoted to a rule: tag it — `(observed: current implementation, unconfirmed as intentional)`.
- **Inferences**: list under `## Assumptions`, never state as authoritative rules.
- **Unknowns** that materially change behavior: ask the user. Otherwise, document the assumption and proceed.

## Specification Content

Section templates for each level live in `references/templates.md` — read it when drafting a new spec file. Summary of the feature template (the most-used one):

```
Purpose · User/Actor · Context · Preconditions · Main Behavior ·
Business Rules · State Changes · Validation · Error Cases · Edge Cases ·
Security Considerations · Acceptance Criteria · Dependencies ·
Non-Goals · Assumptions · Open Questions
```

Include only sections meaningful for the feature. Never add boilerplate to satisfy a template.

### Behavioral Precision

Describe observable behavior, not implementation.

✅ `A patient may cancel an appointment only when it is Scheduled and its start time has not passed.`
❌ `Implement a cancellation service.`

✅ `When cancellation succeeds, the appointment transitions to Cancelled and subsequent cancellation attempts are rejected.`
❌ `Update the appointment status in the database.`

A spec must remain valid if the implementation moves REST→GraphQL, PostgreSQL→another store, React→another framework, monolith→services.

### Requirement Minimalism

Over-specification is upstream over-engineering: every speculative requirement becomes speculative code carrying the authority of the source of truth. Implementation-level minimalism rules cannot remove what the spec mandates. Before admitting any requirement, walk this ladder:

1. **Does it need to exist?** Every requirement must trace to stated user intent, an observed constraint, or an explicit business rule. No orphan requirements admitted because they "seemed professional to include."
2. **Does existing behavior already satisfy it?** Prefer referencing or amending an existing rule over adding a new one.
3. **What is the smallest behavior that satisfies the intent?** No speculative generality: no "configurable," "extensible," "pluggable," or "supports future X" unless the user explicitly required it.
4. **Defer the rest.** Capabilities that might be needed go to **Non-Goals** (binding: do not build) or **Open Questions** (undecided) — never into requirements. A deferred capability listed under Non-Goals is an explicit instruction to implementation agents; one merely omitted is an invitation to infer it.

Minimalism applies to **scope, not rigor**: state models, security requirements, error cases, and edge cases relevant to admitted behavior are precision, not over-building — never cut them in the name of minimalism.

### Acceptance Criteria

Observable, testable, unambiguous, implementation-independent where possible. Use the exact terminology of the state model — if the state is `Cancelled`, write `Cancelled`, not `cancelled`:

```md
- [ ] An authenticated patient can cancel their own future appointment.
- [ ] A patient cannot cancel another patient's appointment.
- [ ] A Completed appointment cannot be cancelled.
- [ ] A Cancelled appointment cannot be cancelled again.
- [ ] A successful cancellation transitions the appointment to Cancelled.
```

Avoid `- [ ] Add POST /appointments/:id/cancel` unless the API contract itself is an explicit requirement — e.g., the API surface is the product, has external consumers, or is versioned. In that case, reference the contract artifact (OpenAPI schema, protobuf definition) as the normative spec for that surface instead of duplicating it in prose. Implementation-level schemas (Zod, ORM models) are never spec artifacts.

### State Modeling

When a feature affects lifecycle, model the state machine explicitly: valid transitions, invalid transitions, transition conditions, terminal states. Never invent states unsupported by requirements or existing behavior.

### Edge Cases & Security

Consult the checklist in `references/checklists.md` (authorization, concurrency, retries, timezones, tenant isolation, abuse prevention, etc.). Include only relevant cases; do not manufacture complexity. Security requirements that affect behavior must be explicit in the spec.

### Non-Goals

Every substantial feature defines what it intentionally does not solve. This prevents scope creep and stops implementation agents from assuming extra requirements.

## Consistency Checking

Before finalizing, compare against `product.md`, relevant domain specs, related feature specs, ADRs, existing behavior, and existing tests. Detect: contradictions, duplicated rules, terminology conflicts, incompatible state transitions, conflicting permissions, incompatible assumptions, missing dependencies.

If a conflict exists, do not silently choose a side. Report it.

## Adversarial Review

After drafting, perform a hostile review:

- What could be misunderstood? Which requirement is ambiguous?
- What behavior is missing? Which edge case invalidates this?
- Which two requirements could conflict?
- **Could two competent developers implement different behavior while both believing they followed this spec?**
- Which acceptance criterion is not objectively testable?
- Does the spec accidentally prescribe implementation?
- Which requirement exists without tracing to stated intent, an observed constraint, or an explicit business rule — and would anything break if it were deleted?
- Does it conflict with existing domain rules?

Fix what the available evidence resolves. Surface what requires human decisions.

## Quality Gate

Ready for human approval only when:

```
[ ] Scope, purpose, and actors are clear
[ ] Behavior is observable; business rules explicit
[ ] Preconditions and invalid behavior defined
[ ] Important edge cases and security implications covered
[ ] Acceptance criteria testable, terminology consistent with state model
[ ] Non-goals explicit; assumptions tagged; open questions listed
[ ] Every requirement traces to intent, constraint, or business rule — no speculative capabilities
[ ] Relevant existing specs checked; no unreported contradictions
[ ] No requirement duplicated across files (references used instead)
[ ] Reviewable by a human in under ~5 minutes without skimming
[ ] Implementation details have not leaked
```

## Modification Rules

1. Read the entire relevant spec.
2. Identify which requirement changes.
3. Check dependent specs (anything linking to it), acceptance criteria, state transitions.
4. Check whether existing behavior contradicts the new requirement.
5. Update the smallest appropriate spec; update links, never copy.
6. Report consequential changes to dependent specs.

**No shadow code**: code changed without a corresponding spec update is a drift event by definition. This matters because an outdated spec is not passively stale — a future agent session, treating the spec as authoritative, will "correct" the working code back to the old behavior. When this skill observes behavior in code/tests that a spec doesn't reflect, it reports it as drift (see Staleness) rather than ignoring it.

## Source of Truth & Staleness

Authority hierarchy:

```
Explicit user decision
  → Approved specification
    → Architectural constraints / ADRs
      → Existing documented behavior
        → Existing implementation and tests
          → AI inference
```

When implementation conflicts with an **approved, current** spec: the implementation is wrong unless the user decides the spec should change.

**Staleness exception**: when an approved spec conflicts with implementation that is *corroborated by passing tests*, treat the spec as suspected drift. Do not assume either side wins. Report the conflict:

```
DRIFT DETECTED
Spec says:            <requirement + file>
Implementation does:  <behavior + evidence (code, passing tests)>
Spec last updated:    <date from frontmatter>
→ Which is correct?
```

When specifications conflict with each other: stop and surface the conflict.

## Do Not Implement

This skill MUST NOT: modify production code, create implementation tasks or plans (including `plan.md` / `tasks.md` — even though they sit in the same feature folder), choose libraries, design APIs for convenience, invent database schemas, refactor code, write tests, or author/modify ADRs. Its write surface is exactly: files under the spec tree that it owns (`product.md`, `domains/*`, `features/*/spec.md`) plus the Specifications pointer section in CLAUDE.md/AGENTS.md. It may inspect code, tests, ADRs, and sibling plan/task files as evidence and identify constraints implementation must respect.

## Output

After creating or updating a spec, report — **omitting fields that are empty**:

```
Specification: <path>            (always)
Scope: Product | Domain | Feature (always)
Created/Updated: <summary>        (always)
Related specs checked: <list>
Key requirements: <summary>
Assumptions: <list>
Open questions: <list>
Conflicts / drift: <list>
Ready for review: yes/no          (always)
```

Never claim a specification is correct merely because it was generated. Never set `status: approved`.

## Guiding Principle

Optimize for clarity, consistency, testability, traceability, minimal ambiguity, minimal duplication, minimal unnecessary detail. The objective is not the longest specification — it is one that lets two independent competent engineers reach substantially the same behavior without guessing.

# Create Specification

You are executing the **SDD Design stage** of the AI-native software development lifecycle.

Your input is the accepted `intent.md`. Your output is a complete, implementation-ready `spec.md` that captures the requirements and design decisions needed for the next stage of the lifecycle.

## Objective

Transform the accepted `intent.md` into a precise requirements-and-design specification.

The resulting `spec.md` must:

- faithfully preserve the intent and desired outcome;
- make implicit requirements explicit;
- define observable acceptance criteria;
- resolve ambiguity where it can be resolved from available evidence;
- identify decisions that require human judgment;
- apply all relevant organizational policies, standards, architecture principles, and domain knowledge;
- describe the proposed solution at the appropriate architectural level;
- identify risks, conflicts, dependencies, and constraints;
- provide enough information for an engineer to create an implementation `plan.md` without rediscovering the requirements.

Do **not** implement the solution.

---

## 1. Read the intent

Read `intent.md` completely before designing the solution.

Treat it as the authoritative statement of:

- the problem;
- desired outcome;
- users and stakeholders;
- affected systems;
- constraints;
- explicit non-goals;
- open questions;
- success criteria.

Do not silently change the product intent.

If the intent is internally contradictory, incomplete, or ambiguous, preserve the original intent and flag the issue rather than inventing a product decision.

---

## 2. Inspect the repository and existing system

Before proposing technical design, inspect the existing codebase and relevant documentation.

Determine:

- existing architecture;
- relevant modules and boundaries;
- existing domain concepts;
- existing APIs and integrations;
- existing data models;
- authentication and authorization mechanisms;
- existing patterns and conventions;
- existing infrastructure;
- testing strategy;
- observability and operational conventions;
- relevant configuration;
- existing implementations that should be extended rather than duplicated.

Prefer existing repository conventions over introducing new abstractions.

Do not propose a design based solely on generic best practices when the repository provides concrete evidence.

---

## 3. Load and apply organizational knowledge

Use all applicable organizational `CLAUDE.md` files and skills.

Skills represent institutional knowledge and must be treated as **constraints on the design**, not merely suggestions.

Apply relevant skills for areas such as:

- architecture;
- security;
- authentication;
- authorization;
- privacy;
- compliance;
- accessibility;
- UX;
- API design;
- data modeling;
- observability;
- testing;
- infrastructure;
- performance;
- reliability;
- domain-specific policies.

When multiple policies apply, identify conflicts explicitly.

Never silently weaken or bypass an organizational policy.

---

## 4. Separate requirements from design decisions

Distinguish clearly between:

### Requirements

What the system must accomplish.

Requirements should be:

- observable;
- testable where possible;
- traceable to `intent.md`;
- independent of unnecessary implementation details.

### Design decisions

How the system will satisfy those requirements.

Design decisions should explain:

- the chosen approach;
- why it fits the existing system;
- relevant alternatives considered;
- important trade-offs.

Do not introduce technical decisions merely for the sake of architectural sophistication.

---

## 5. Define scope

Explicitly establish:

### In scope

Capabilities and behavior required to satisfy the intent.

### Out of scope

Capabilities intentionally excluded from this change.

### Assumptions

Assumptions made because the available evidence supports them.

### Dependencies

External systems, teams, services, data, infrastructure, policies, or decisions required for the solution.

Do not turn assumptions into requirements without evidence.

---

## 6. Define functional requirements

Describe the required system behavior.

For each significant requirement, specify:

- actor;
- trigger;
- preconditions;
- expected behavior;
- resulting state;
- failure behavior;
- relevant business rules;
- authorization requirements where applicable.

Requirements should describe **observable behavior**, not implementation tasks.

Avoid vague requirements such as:

> "The system should handle authentication properly."

Prefer requirements that can actually be verified.

---

## 7. Define non-functional requirements

Identify applicable requirements for:

- security;
- privacy;
- performance;
- availability;
- reliability;
- scalability;
- accessibility;
- observability;
- maintainability;
- compatibility;
- compliance;
- cost.

Only include requirements that are relevant to the change.

Do not manufacture arbitrary targets when the organization has not defined them.

When a target is unknown but materially affects the design, flag it as an unresolved decision.

---

## 8. Design the solution

Describe the proposed design at the level required for engineering planning.

Cover the relevant areas:

- system boundaries;
- components;
- responsibilities;
- domain boundaries;
- data flow;
- control flow;
- APIs/interfaces;
- data models;
- persistence;
- external integrations;
- authentication;
- authorization;
- error handling;
- state transitions;
- events/messages;
- configuration;
- observability;
- deployment/runtime considerations.

Respect existing architectural boundaries.

Do not prescribe individual file changes unless they are necessary to communicate an architectural constraint. File-level implementation planning belongs primarily to `plan.md`.

---

## 9. Evaluate architectural integrity

Check the proposed design against the organization's architectural standards.

In particular, evaluate:

- separation of concerns;
- dependency direction;
- dependency inversion;
- domain boundaries;
- coupling;
- cohesion;
- extensibility;
- testability;
- failure isolation;
- security boundaries;
- authorization boundaries;
- data ownership;
- API boundaries.

Do not apply patterns mechanically.

A pattern should be introduced only when it solves a concrete problem in the proposed design.

---

## 10. Security and policy analysis

Perform an explicit security analysis.

Consider, where applicable:

- authentication;
- authorization;
- privilege boundaries;
- trust boundaries;
- input validation;
- output encoding;
- sensitive data;
- secrets;
- session management;
- injection risks;
- abuse cases;
- data exposure;
- auditability;
- third-party integrations;
- least privilege.

Identify any security requirement that cannot be satisfied by the proposed design.

Do not silently trade away security requirements for implementation convenience.

---

## 11. Identify concerns and unresolved decisions

Create a dedicated **Concerns & Decisions** section.

Flag:

- missing requirements;
- ambiguous intent;
- contradictory requirements;
- policy conflicts;
- architectural conflicts;
- security concerns;
- compliance concerns;
- UX concerns;
- significant technical risks;
- external dependencies;
- assumptions with material consequences;
- decisions requiring product-owner approval;
- decisions requiring technical/security/domain-owner approval.

For every significant concern, state:

1. **Issue**
2. **Why it matters**
3. **Available options**, when known
4. **Recommended option**, when one is clearly preferable
5. **Required decision owner**

Do not hide uncertainty.

Do not invent an answer merely to make the specification appear complete.

---

## 12. Traceability

Every significant requirement must be traceable back to the intent.

Every significant design decision must be traceable to:

- a requirement;
- an organizational policy;
- an existing system constraint;
- or an explicitly documented assumption.

The specification must make it possible to answer:

> "Why is this in the design?"

---

## 13. Acceptance criteria

Define concrete acceptance criteria for the resulting behavior.

Acceptance criteria should allow a future implementation and its tests to determine whether the requirement has been satisfied.

Cover:

- primary success paths;
- important alternate paths;
- failure cases;
- authorization/security behavior;
- relevant edge cases;
- applicable non-functional constraints.

Do not write implementation-specific test cases unless necessary to clarify behavior.

---

## 14. Prepare the handoff to Build

The specification will be consumed by an engineer/agent in the next SDD stage.

Therefore, ensure that an engineer can answer from `spec.md`:

- What are we building?
- Why are we building it?
- What behavior is required?
- What is explicitly out of scope?
- What constraints apply?
- What architectural boundaries must be preserved?
- What decisions have already been made?
- What decisions remain unresolved?
- What risks must be considered?
- How will we know the implementation is correct?

The next stage should be able to produce `plan.md` without having to rediscover the product requirements.

---

# Output

Produce exactly one artifact:

`spec.md`

The specification should normally contain:

1. Overview
2. Problem & Desired Outcome
3. Scope
4. Users & Stakeholders
5. Functional Requirements
6. Non-Functional Requirements
7. Business Rules
8. Proposed Design
9. Architecture & Boundaries
10. Data & Integrations
11. Security & Policy Considerations
12. UX / Accessibility Considerations
13. Acceptance Criteria
14. Dependencies & Assumptions
15. Alternatives & Trade-offs
16. Concerns & Unresolved Decisions
17. Traceability to Intent

Adapt the structure when the change does not require a section.

Do not add sections merely to satisfy the template.

---

# Critical Rules

- `intent.md` is the source of product intent.
- Organizational skills are enforceable design constraints.
- Existing repository architecture is evidence.
- Do not invent consequential requirements.
- Do not silently resolve material ambiguity.
- Do not silently violate organizational policies.
- Do not implement code.
- Do not create an implementation plan; that belongs to the next stage.
- Do not optimize for architectural complexity.
- Prefer the simplest design that satisfies the requirements and constraints.
- Flag uncertainty rather than hiding it.
- Human approval is required for consequential product, security, compliance, and architectural decisions.
- `spec.md` must be suitable for version control and human review.
- The resulting specification must be understandable independently of this conversation.

Before finalizing `spec.md`, perform a final consistency check:

1. Does the design actually solve the problem stated in `intent.md`?
2. Are all explicit requirements addressed?
3. Are all constraints respected?
4. Are open questions answered or explicitly carried forward?
5. Are policy conflicts surfaced?
6. Are consequential assumptions flagged?
7. Are acceptance criteria testable?
8. Can the next stage create a `plan.md` without rediscovering the requirements?
9. Have unnecessary complexity and speculative architecture been avoided?

If any answer is "no", correct the specification or flag the issue rather than silently proceeding.
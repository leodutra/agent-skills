# Spec Section Templates

Include only sections meaningful for the artifact. Never add boilerplate to satisfy a template. Every file starts with the metadata frontmatter defined in SKILL.md (`status`, `updated`).

## Product Specification

```md
# Product

## Purpose
## Users
## Core Capabilities
## Global Business Rules
## Global Constraints
## Compliance
## Quality Attributes
## Non-Goals
## Assumptions
## Open Questions
```

Non-Goals carries MVP scope as `post-MVP: ...` — scope is content, not a separate document.

## Domain Specification

```md
# Domain

## Purpose
## Concepts
## Actors
## Invariants
## Business Rules
## Lifecycle / State Model
## Relationships
## Domain Constraints
## Non-Goals
## Assumptions
## Open Questions
```

Written only when a rule is shared by 2+ features. Relationships links adjacent domains — it never restates their rules.

## Feature Specification

Sections and their order: see the feature list in SKILL.md § Specification Content. Notes on the ones that are filled in wrong most often:

- **Main Behavior** — the success path as observable outcome. Numbered steps only when ordering is itself a requirement.
- **State Changes** — the domain's exact state terminology (`Cancelled`, not `cancelled`). What becomes true, and what becomes impossible.
- **Error Cases** — condition → observable outcome. Errors are behavior; status codes and exception types are not, unless the API contract is itself an explicit requirement.
- **Business Rules** — only rules specific to this feature. Shared rules are linked to their domain spec.
- **Non-Goals** — binding: an implementation agent reads this as "do not build".
- **Assumptions** — inferences. Observed-but-unconfirmed behavior is tagged inline where it appears: `(observed: current implementation, unconfirmed as intentional)`.

## Traceability in derived specs

In DERIVE mode, every requirement cites the `product.md` requirement it decomposes, so the "no orphan requirements" gate is mechanically checkable:

```md
Cancellation is available to the patient who owns the appointment.
(decomposes: [product.md — Self-service scheduling](../../../product.md#core-capabilities))
```

# Authorization — the Permit Pattern

**Authorization MUST be a typed decision taken at the entry of a use case, inside the slice that owns the action: `action.can(actor) -> Permit<G>`.** Entities protect business invariants; the action's authorization protects who may execute it. You MUST NOT use scattered role checks, and you MUST NOT reduce the decision to a `bool`. (Keyword conventions: see SKILL.md. Tags `(n)` name the deriving principle in `first-principles.md`.)

Derivation: identity and permission are inputs (7); who may act is a decision that belongs with one authority (6); a permission is a fact with a validity frame (2); a capability held is a receipt, while a role checked at each site is the same proof re-paid from memory at every use (1); and a decision reduced to a bit discards both its reason and the artifact it established (1, 3) — so the decision's result is a type, not a flag.

## Vocabulary

| Term | Meaning |
| --- | --- |
| `Permission` | a capability or fact the actor **has** — an input to policy |
| `Can` | the protocol that evaluates one action for one actor |
| `Permit<G>` | the typed **result** of that decision |
| `Denial` | why it was not granted |
| Grant (`G`) | the value a granted permit carries forward |

A permission is an input; a permit is an output. You MUST NOT conflate them.

## Separate authN from authZ

(3 — distinct meanings, distinct representations) Authentication = "who are you?"; authorization = "may you do this?" You MUST NOT mix them in one check.

## Actor (domain type)

(2 — evidence can travel, acceptance cannot; 7) The domain MUST depend on an `Actor`, NEVER on JWT/cookies/OAuth/framework. The token is portable evidence; verifying it and producing an `Actor` is the act of acceptance, and it happens ONCE at the boundary. Then pass the `Actor` inward as an ordinary input.

```text
Actor { id: UserId, permissions: Set<Permission> }
```

**The Actor has a validity frame** (2; A4 — the permission the model calls granted may have lapsed). An `Actor` is valid for the request that resolved it. A long-lived process, a queued job, or a cached permission set MUST NOT reuse an `Actor` past its frame; re-resolve at the next crossing.

## Authorize by capability, not role

(1, 6) You MUST check capabilities (`Permission::CancelAppointment`) and MUST NOT branch on roles (`if role == "admin"`). Roles are ONLY **groupings of permissions**, assigned at the edge in data:

```text
Admin => [ApproveOrder, RefundOrder, CancelOrder]
```

The role → permission mapping has one authoritative home (6); a role conditional in code is a second copy of it that will drift. Adding or changing a role MUST be a data change, not a code change (13).

## The `Can` protocol

(3, 5 — one narrow contract instead of a family of ad-hoc functions) The action is the receiver and supplies the meaning; `can` supplies the uniform interface.

```rust
pub trait Can<A> {
    type Grant;
    fn can(&self, actor: &A) -> Permit<Self::Grant>;
}

CancelAppointment { appointment_id }.can(&actor)   // not can_cancel_appointment(&actor, id)
```

`can` is reserved for this protocol. Business eligibility reads `is_refundable`, `is_eligible` (see `domain-modeling.md`).

## `Permit` and `Denial`

```rust
pub enum Permit<G = ()> { Granted(G), Denied(Denial) }

pub enum Denial {
    NotAllowed(Reason),   // this actor would not be authorized even in a valid target state
    NotPossible(Reason),  // authorized, but the current state forbids the action
}
```

`Permit` MUST be its own type, not an alias for `Result`: `Result` means an operation succeeded or failed; `Permit` means a decision was granted or denied (3 — distinct meanings, distinct representations).

**Classification rule** (counterfactual): if only the target's state changed to an otherwise valid one, would this actor be authorized? No → `NotAllowed`. Yes → `NotPossible`. The two MUST stay distinct: they drive transport status, UI, retry, idempotency, and diagnostics differently.

`Reason` MUST be structured domain data (an enum, carrying context where it matters — `MissingPermission(Permission)`, `NotMemberOfClinic(ClinicId)`, `AlreadyCancelled`), NEVER free text, and MUST NOT name a transport (9, 2 — each frame receives failure in its own vocabulary).

**Deny by default** (2, 4) — a feature is locked unless a capability grants it; the match over permissions is exhaustive and the fall-through arm is `Denied`.

## Graduated grants — take the weakest one that works

(1 — carry the receipt; frame — an abstraction must earn its existence) `G` is the extensibility point. You SHOULD use the weakest form the action actually needs:

| Grant | Use |
| --- | --- |
| `Permit<()>` | plain decision — UI affordances, simple commands |
| `Permit<Filter>` / `Permit<Scope>` | a read: the **constrained query** the actor may run (tenant, clinic, provider, patient, date, field scope) |
| `Permit<DomainGrant>` | a mutation whose execution needs the decision's artifact (ids, actor, revision) |

```rust
let filter = ListAppointments { clinic_id }.can(&actor).granted()?;
repository.list(filter)?;                    // authorized scope, applied as a predicate

let grant = CancelAppointment { appointment_id }.can(&actor).granted()?;
appointments.cancel(grant)?;                 // execution consumes the decision's artifact
```

A read grant is authorization to execute a constrained query — NOT a snapshot of authorized rows (2 — a fact's frame ends; re-read under the filter).

`is_granted()` is for affordances (showing a button). It is NOT a security boundary and MUST NOT stand as proof that a later command may execute.

A dedicated non-forgeable capability (`Warrant<CancelAppointment>`: private construction, bound to one action instance, consumed on execution) is an OPTIONAL extension (12 — typestate). You MUST NOT introduce it without a demonstrated need; simple actions stay simple.

## API

```rust
impl<G> Permit<G> {
    fn is_granted(&self) -> bool;
    fn is_denied(&self) -> bool;
    fn granted(self) -> Result<G, Denial>;   // the one crossing into ordinary error flow
    fn map<U>(self, f: impl FnOnce(G) -> U) -> Permit<U>;
    fn and_then<U>(self, f: impl FnOnce(G) -> Permit<U>) -> Permit<U>;
}
```

`granted()`, not `ok()` — `Result::ok()` already means something else. The API SHOULD borrow `Result`'s useful algebra and keep authorization's own vocabulary (`map_denied`, not `map_err`); it MUST NOT be grown into a copy of `Result`. There is no generic `and()`: which denial wins is a policy question, not a combinator's.

Composition is sequential and fail-fast — the first failed check determines the denial, and each reason stays next to the predicate that produces it:

```rust
Permit::check(actor.has(Permission::CancelAppointment), Denial::NotAllowed(Reason::MissingPermission))
    .check(actor.member_of(clinic_id),                  Denial::NotAllowed(Reason::NotMemberOfClinic))
    .check(appointment.is_cancellable(),                Denial::NotPossible(Reason::AlreadyCancelled))
    .grant(grant)
```

Helpers — the builder above, or a derive macro — MUST make the policy easier to read, never hide it: the conceptual implementation stays ordinary code a reader can follow. A macro is an ergonomic optimisation, OPTIONAL and outside the core (frame — an abstraction must earn its existence).

## The decision is pure

(7 — receive dependencies, do not discover them) `can` MUST evaluate information already available: actor traits, action fields, loaded aggregates, results already fetched from an external policy engine (OPA/Cedar/SpiceDB). It MUST NOT perform hidden I/O. Acquisition happens first, in the slice's shell:

```text
load context → can() → Permit → grant → atomic execution
```

An explicit `Facts` type, a `Rule`/specification abstraction, and an async `Can` are OPTIONAL extensions, admitted only when the policy's complexity earns them (frame). Trait bounds (`impl<A: HasPermissions + MemberOf<Clinic>> Can<A> for CancelAppointment`) state **context completeness** — the actor type supplies what the decision needs — and MUST NOT be described as compile-time proof that this actor may perform this action. Aggregate capability traits (`CanManageAppointments`) MAY group bounds ONLY when they name a real domain capability, never to hide generics.

## A permit is not a lock

(11, 12 — authorization and concurrency are different obligations) The decision is taken at a point in time and does not reserve the world. The execution boundary MUST enforce, atomically, the state assumptions that matter to the operation:

```sql
UPDATE appointments SET status = 'cancelled'
WHERE id = ? AND status = 'scheduled';        -- the predicate IS the invariant
```

Use the predicate the invariant demands; do NOT invalidate an authorization decision because an unrelated column changed. Whether an already-cancelled appointment is a `NotPossible` denial or a successful no-op is the action's own idempotency decision (10), not the pattern's.

## Placement — inside the slice (13, 14)

Authorization lives with the action whose policy it defines. There is NO module-wide `policies/can_*` grouping and no central authorization object holding unrelated policies: that is the god-context defect (ledger) wearing an auditor's badge, and it separates a decision from the only code that changes with it.

```text
appointments/
├── cancel-appointment/
│   ├── command            # the action type
│   ├── authorization      # impl Can — MAY stay in the command file while small
│   ├── handler
│   └── tests
├── reschedule-appointment/
├── list-appointments/
└── domain/                # Permission, Reason, actor capability traits, shared value objects
```

`Permission`, `Reason`, and actor capability traits are shared vocabulary and belong in `domain/` (or the kernel when several modules name them). Only a genuinely shared decision — the same policy evaluated by 2+ slices — graduates to `policies/` (6 — one home the moment a second copy would exist). A small slice MAY keep command, authorization, and handler in one file; you SHOULD NOT pre-split.

## Transport, audit, break-glass

- **Transport mapping is outside the domain** (2, 9): typically `NotAllowed → 403`, `NotPossible → 409`, translated at the edge. `Denial` MUST NOT carry status codes.
- **Conversion**: `let grant = action.can(&actor).granted()?;` with `From<Denial>` for the application error when the denial already carries enough context, or an explicit `from_denial(&action, &actor, denial)` when action, actor, or resource context is needed.
- **Observable** (1 — execution leaves receipts): security-sensitive decisions — grants included — MUST be loggable with action, actor, target, decision, reason, relevant revision, and correlation id. A `Permit` need not become a persisted or signed receipt to support this.
- **Break-glass and impersonation** (2, 6): `EmergencyAccess`, `Impersonation`, `SupportOverride` MUST be authorization **inputs** flowing through `can`, with their reason recorded. `if admin { bypass }` is a defect.
- **Growth path** (13 — escalate on evidence): capabilities → ABAC when attributes matter → ReBAC for relationships. Escalate ONLY when needed.

## Testing

(frame, rung 2) Authorization MUST be testable without infrastructure — build the actor and context directly and assert on the permit.

- **Decision**: `assert!(action.can(&actor).is_granted())`, and negative cases as first-class, asserting the *semantic* denial: missing permission → `NotAllowed(MissingPermission)`; wrong clinic → `NotAllowed(NotMemberOfClinic)`; already cancelled → `NotPossible(AlreadyCancelled)`.
- **Execution**: a valid grant produces the state transition; a stale or conflicting state produces the concurrency/domain error — proving the permit is not the lock.
- **Integration**: context acquisition → `can` → grant → atomic execution, once per security-sensitive path.

## Non-goals

The pattern does NOT provide authentication, identity management, a policy language, transactions, general concurrency control, transport error handling, or cryptographic proof. It provides one thing: a uniform typed protocol for an authorization decision that carries forward, when useful, the artifact that decision established.

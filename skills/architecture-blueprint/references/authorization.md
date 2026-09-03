# Authorization

**Authorization MUST be a domain policy applied at the entry of a use case. Entities protect business invariants; policies protect who may execute an action.** You MUST NOT use scattered role checks. (Keyword conventions: see SKILL.md. Tags `(n)` name the deriving principle in `first-principles.md`.)

Derivation: identity and permission are inputs (7); who may act is a decision that belongs with one authority (6); a permission is a fact with a validity frame (2); a capability held is a receipt, while a role checked at each site is the same proof re-paid from memory at every use (1).

## Separate authN from authZ

(3 — distinct meanings, distinct representations) Authentication = "who are you?"; authorization = "may you do this?" You MUST NOT mix them in one check.

## Actor (domain type)

(2 — evidence can travel, acceptance cannot; 7) The domain MUST depend on an `Actor`, NEVER on JWT/cookies/OAuth/framework. The token is portable evidence; verifying it against this frame's trust anchors and producing an `Actor` is the act of acceptance, and it happens ONCE at the boundary. Then pass the `Actor` inward as an ordinary input.

```text
Actor { id: UserId, permissions: Set<Permission> }
```

**The Actor has a validity frame** (2 — the clock is a frame; A4 — the permission the model calls granted may have lapsed). An `Actor` is valid for the request that resolved it. A long-lived process, a queued job, or a cached permission set MUST NOT reuse an `Actor` past its frame; re-resolve at the next crossing.

## Authorize by capability, not role

(1, 6) You MUST check capabilities (`Permission::ApproveOrder`) and MUST NOT branch on roles (`if role == "admin"`). Roles are ONLY **groupings of permissions**, assigned at the edge in data:

```text
Admin => [ApproveOrder, RefundOrder, CancelOrder]
```

The role → permission mapping has one authoritative home (6); a role conditional in code is a second copy of it that will drift. Adding or changing a role MUST be a data change, not a code change (13 — separate stable meaning from unstable mechanism).

## Policy = a `can*` pure function

(7, 6; the `can*` name is *convention*) Authorization MUST be one named function per action. It MUST take **full context**:

```text
canApproveOrder(actor, order) -> bool =
    actor.has(ApproveOrder)
    && order.total < 10000
```

The function MUST be pure: no DB, no HTTP, no JWT, no framework, no clock it did not receive. The use case loads the context and hands it over (7 — receive dependencies; do not discover them). The policy decides about the *actor*; whether the order's state permits approval is the entity's own invariant and MUST NOT be duplicated here (6 — one authoritative home).

## Use case calls the policy at entry; the entity stays out of it

(6 — decisions live with the authority over their subject) The use case MUST load the resource, check the policy, then act. You MUST NOT put authorization on the entity (`order.approve(actor)`) — that couples the domain to IAM/RBAC, and gives the entity authority over a question that is not its subject.

```text
order = load(cmd.orderId)
ensure(canApproveOrder(actor, order), Unauthorized)
order.approve()          // entity guards ONLY its own business invariants
```

`order.approve()` answers whether the order may be approved given its state; `canApproveOrder` answers whether the actor may approve it.

## Structure

You SHOULD group `can*` policies in a module `policies/` folder (or beside each slice). This is an EXCEPTION to the "policies/ only when shared by 2+ slices" rule: authorization `can*` policies MAY live in `policies/` even when slice-specific, because their audience — an auditor asking "who may do what" — reads them together (14 — what is needed to verify a thing lives near the thing).

```text
orders/
├── approve-order/
├── refund-order/
├── cancel-order/
└── policies/
    ├── can-approve-order
    ├── can-refund-order
    └── can-cancel-order
```

## Other practices

- **Deny by default** (2 — what crosses a boundary is untrusted until accepted; 4 — the unhandled arm is a state, and it is *Deny*). A feature MUST be locked unless a capability grants it; an unhandled case MUST deny. The match over permissions is exhaustive, and the fall-through arm is *Deny*.
- **Growth path** (13 — escalate on evidence): RBAC/capabilities → **ABAC** when attributes matter (`actor.department == order.department`) → **ReBAC** for relationships (owns document, manages team, member of project; common in SaaS). You SHOULD escalate ONLY when needed.
- **Observable/auditable** (1 — execution leaves receipts) — you MUST log allow/deny with correlation IDs (see `events-and-consistency.md`).
- **Test negative cases as first-class** (frame, rung 2) — you MUST cover them: "given a principal without `RefundOrder`, when a refund is requested, then it is denied."

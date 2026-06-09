# Authorization

**Authorization MUST be a domain policy applied at the entry of a use case. Entities protect business invariants; policies protect who may execute an action.** You MUST NOT use scattered role checks. (Keyword conventions: see SKILL.md.)

## Separate authN from authZ

Authentication = "who are you?"; authorization = "may you do this?" You MUST NOT mix them in one check.

## Actor (domain type)

The domain MUST depend on an `Actor`, NEVER on JWT/cookies/OAuth/framework. Resolve the token into an `Actor` at the boundary, then pass it inward.

```text
Actor { id: UserId, permissions: Set<Permission> }   // and/or roles
```

## Authorize by capability, not role

You MUST check capabilities (`Permission::ApproveOrder`) and MUST NOT branch on roles (`if role == "admin"`). Roles are ONLY **groupings of permissions**, assigned at the edge in data:

```text
Admin => [ApproveOrder, RefundOrder, CancelOrder]
```

Adding or changing a role MUST be a data change, not a code change.

## Policy = a `can*` pure function

Authorization MUST be one named `can*` function per action. It MUST take **full context**:

```text
canApproveOrder(actor, order) -> bool =
    actor.has(ApproveOrder)
    && order.status == Pending
    && order.total < 10000
```

The function MUST be pure: no DB, no HTTP, no JWT, no framework.

## Use case calls the policy at entry; the entity stays out of it

The use case MUST load the resource, check the policy, then act. You MUST NOT put authorization on the entity (`order.approve(actor)`) — that couples the domain to IAM/RBAC.

```text
order = load(cmd.orderId)
ensure(canApproveOrder(actor, order), Unauthorized)
order.approve()          // entity guards ONLY its own business invariants
```

`order.approve()` answers whether the order may be approved given its state; `canApproveOrder` answers whether the actor may approve it.

## Structure

You SHOULD group `can*` policies in a module `policies/` folder (or beside each slice). This is an EXCEPTION to the "policies/ only when shared by 2+ slices" rule: authorization `can*` policies MAY live in `policies/` even when slice-specific.

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

- **Deny by default.** A feature MUST be locked unless a capability grants it; an unhandled case MUST deny.
- **Growth path:** RBAC/capabilities → **ABAC** when attributes matter (`actor.department == order.department`) → **ReBAC** for relationships (owns document, manages team, member of project; common in SaaS). You SHOULD escalate ONLY when needed.
- **Observable/auditable** — you MUST log allow/deny with correlation IDs (see `events-and-consistency.md`).
- **Test negative cases as first-class** — REQUIRED: "given a principal without `RefundOrder`, when a refund is requested, then it is denied."

# Authorization

**Authorization is a domain policy applied at the entry of a use case. Entities protect business invariants; policies protect who may execute an action.** Scattered role checks duplicate, contradict, and resist audit — avoid them.

## Separate authN from authZ

Authentication = "who are you?"; authorization = "may you do this?" Never mix them in one check.

## Actor (domain type)

The domain depends on an `Actor`, never on JWT/cookies/OAuth/framework. Resolve the token into an `Actor` once at the boundary, then pass it inward.

```text
Actor { id: UserId, permissions: Set<Permission> }   // and/or roles
```

## Authorize by capability, not role

Check capabilities (`Permission::ApproveOrder`), never role conditionals (`if role == "admin"`) — capabilities change less than roles. Roles are just **groupings of permissions**, assigned at the edge in data:

```text
Admin => [ApproveOrder, RefundOrder, CancelOrder]
```

Adding or changing a role becomes a data change, not a code change.

## Policy = a `can*` pure function

One named function per action, taking **full context** — authorization rarely depends on the actor alone (it also depends on resource state and business attributes):

```text
canApproveOrder(actor, order) -> bool =
    actor.has(ApproveOrder)
    && order.status == Pending
    && order.total < 10000
```

Pure: no DB, no HTTP, no JWT, no framework. Centralized, testable, auditable.

## Use case calls the policy at entry; the entity stays out of it

Load the resource, check the policy, then act. Do **not** put authorization on the entity (`order.approve(actor)`) — that couples the domain to IAM/RBAC.

```text
order = load(cmd.orderId)
ensure(canApproveOrder(actor, order), Unauthorized)
order.approve()          // entity guards only its own business invariants
```

Complements `domain-modeling.md`: `order.approve()` answers "can this order be approved given its state?"; `canApproveOrder` answers "may this actor approve it?" — two different questions, two different homes.

## Structure

Group `can*` policies in a module `policies/` folder (or beside each slice). Grouping is justified here by **auditability** — every authorization rule visible in one place — even when a policy serves a single slice.

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

- **Deny by default** — locked unless a capability grants it; an unhandled case denies.
- **Growth path:** RBAC/capabilities → **ABAC** when attributes matter (`actor.department == order.department`) → **ReBAC** for relationships (owns document, manages team, member of project; common in SaaS). Escalate only when needed.
- **Observable/auditable** — log allow/deny with correlation IDs (see `events-and-consistency.md`).
- **Test negative cases as first-class**: actor without `ApproveOrder` → denied.

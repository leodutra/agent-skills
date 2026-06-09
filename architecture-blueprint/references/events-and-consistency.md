# Events & Consistency

Cross-module communication, direct-call-vs-event, consistency, observability. (Keyword conventions: see SKILL.md.)

## Domain events

Events MUST be past-tense business **facts**. Consumers: Inventory, Shipping, Notifications, Analytics.

```text
OrderApproved   OrderCancelled   OrderRefunded   InventoryReserved
```

You MUST NOT emit vague mutations (`OrderUpdated`, `EntityChanged`).

## Direct call vs. event

You SHOULD use a **direct call** when: same transaction, same invariant, or immediate (strong) consistency.
You SHOULD use an **event** when: another module merely reacts, eventual consistency is acceptable, and coupling should drop.

You SHOULD decide consistency first, then coupling.

## Consistency model

Every interaction MUST declare its consistency requirement (in the module README, and an ADR where it matters).

```text
Order creation         → Strong
Inventory reservation  → Strong
Email notification     → Eventual
Analytics update       → Eventual
```

Any handler crossing an eventual boundary (events, queues, retries) MUST be idempotent — see `domain-modeling.md`.

## Observability

Important workflows MUST be reconstructable. Emit milestones (`OrderCreated`, `OrderApproved`, `InventoryReserved`, `PaymentCaptured`) with:

- **Structured logging** (machine-parseable fields) — REQUIRED.
- **Correlation IDs** threaded through the whole workflow, across modules and async hops — REQUIRED.
- **Traceability** — the workflow path MUST be recoverable.
- **Event visibility** — emitted facts MUST be recorded.

You MUST be able to reconstruct exactly what happened to one order, in order, from telemetry alone.

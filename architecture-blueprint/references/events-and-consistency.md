# Events & Consistency

Cross-module communication, direct-call-vs-event, consistency, observability.

## Domain events

Events are past-tense business **facts**. Consumers: Inventory, Shipping, Notifications, Analytics.

```text
OrderApproved   OrderCancelled   OrderRefunded   InventoryReserved
```

Avoid vague mutations (`OrderUpdated`, `EntityChanged`) — a consumer can't act on them. Name the fact, not the table write.

## Direct call vs. event

**Direct call** when: same transaction, same invariant, or immediate (strong) consistency.
**Event** when: another module merely reacts, eventual consistency is acceptable, and coupling should drop.

Trade-off: direct calls = immediate consistency + clear call graph but tight coupling; events = decoupling + load absorption but eventual consistency + idempotent handlers required. Decide on consistency first, then coupling.

## Consistency model

Every interaction **declares** its requirement (in the module README, and an ADR where it matters).

```text
Order creation         → Strong
Inventory reservation  → Strong
Email notification     → Eventual
Analytics update       → Eventual
```

Explicit declaration prevents over-strong (a notification blocking checkout) and under-strong (inventory drift) failures. Anything crossing an eventual boundary (events, queues, retries) needs **idempotent** handlers — see `domain-modeling.md`.

## Observability

Important workflows must be reconstructable. Emit milestones (`OrderCreated`, `OrderApproved`, `InventoryReserved`, `PaymentCaptured`) with:

- **Structured logging** (machine-parseable fields).
- **Correlation IDs** threaded through the whole workflow, across modules and async hops.
- **Traceability** — the workflow path is recoverable.
- **Event visibility** — emitted facts are recorded.

Test: from telemetry alone, can you reconstruct exactly what happened to one order, in order? If not, it's under-observed.

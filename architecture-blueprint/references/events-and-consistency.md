# Events & Consistency

How modules communicate, how to decide between direct calls and events, how to declare consistency, and how to keep workflows observable. Read this when wiring cross-module interactions or reviewing coupling and consistency.

## Domain events

Events communicate **facts** between modules. They are named in the past tense and express something that happened in the business.

```ts
publish(OrderCreated)
```

Typical consumers of an order event: Inventory, Shipping, Notifications, Analytics.

Prefer specific business facts:

```text
OrderApproved
OrderCancelled
OrderRefunded
InventoryReserved
```

Avoid vague mutation events that carry no business meaning:

```text
OrderUpdated
EntityChanged
```

A consumer can react meaningfully to `OrderRefunded`; it cannot tell what to do with `OrderUpdated`. Name the fact, not the table write.

## Direct call vs. event — how to decide

Use a **direct call** when:

- the work happens in the same transaction,
- it guards the same invariant, or
- it requires immediate (strong) consistency.

Use an **event** when:

- another module merely reacts to something,
- eventual consistency is acceptable, and
- you want to reduce coupling between the modules.

The trade-off: direct calls give you immediate consistency and a clear call graph but couple modules tightly; events decouple modules and absorb load but introduce eventual consistency and the need for idempotent handlers. Choose based on the consistency requirement first, then coupling.

## Consistency model

Every interaction must **declare** its consistency requirement. Make it explicit in the module README and, where it matters, in an ADR.

```text
Order creation         → Strong consistency
Inventory reservation  → Strong consistency
Email notification     → Eventual consistency
Analytics update       → Eventual consistency
```

Being explicit prevents two classic failures: accidentally making a fire-and-forget notification block a checkout (over-strong), and accidentally letting inventory drift because a reservation was treated as eventual (under-strong). State the requirement; don't let it emerge by accident from implementation details.

Anything crossing an eventual-consistency boundary (events, queues, retries) must have **idempotent** handlers — see `domain-modeling.md` (Idempotency).

## Observability

Every important workflow must be observable so it can be reconstructed after the fact. Emit visibility for the key business milestones:

```text
OrderCreated
OrderApproved
OrderCancelled
InventoryReserved
PaymentCaptured
```

Requirements:

- **Structured logging** — machine-parseable fields, not free-text prose.
- **Correlation IDs** — one id threaded through a whole workflow so its steps can be stitched together across modules and async hops.
- **Traceability** — the path of a request/workflow is recoverable.
- **Event visibility** — emitted business facts are recorded.

The test of good observability: given a customer complaint, can you reconstruct exactly what happened to their order, in order, from the telemetry alone? If not, the workflow is under-observed.

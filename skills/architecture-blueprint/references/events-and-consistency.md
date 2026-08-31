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

## Concurrency & cancellation

**Cancellation is control flow, not an error case.** Long-running or externally triggered work MUST propagate cancellation: when a request or job is abandoned, its child operations MUST be cancelled and its resources released. Thread the cancellation signal (Rust `CancellationToken`, Go `context.Context`, JS `AbortSignal`) exactly as correlation IDs are threaded. Orphaned work still running after its caller is gone is a defect. A cancelled operation MUST leave state consistent — partial effects MUST be compensated or safely retryable (see idempotency in `domain-modeling.md`).

**Independent work SHOULD run concurrently, and MUST be bounded.** Where N operations do not depend on each other, fan out rather than sequencing them — with an explicit concurrency limit. Unbounded fan-out against a shared resource (connection pool, third-party API) MUST NOT be used: it converts a latency win into an outage.

**Scatter-gather** is the default shape for aggregation endpoints:

```text
        ┌→ service A ┐
request ├→ service B ├→ gather → result
        └→ service C ┘
```

You MUST declare per-branch failure behavior: which branches are required, which MAY degrade to a partial result, and the deadline for the whole gather. A gather with no timeout is permanently as slow as its slowest branch.

## Observability

Important workflows MUST be reconstructable. Emit milestones (`OrderCreated`, `OrderApproved`, `InventoryReserved`, `PaymentCaptured`) with:

- **Structured logging** (machine-parseable fields) — REQUIRED.
- **Correlation IDs** threaded through the whole workflow, across modules and async hops — REQUIRED.
- **Traceability** — the workflow path MUST be recoverable.
- **Event visibility** — emitted facts MUST be recorded.

You MUST be able to reconstruct exactly what happened to one order, in order, from telemetry alone.

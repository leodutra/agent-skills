# Events & Consistency

Cross-module communication, direct-call-vs-event, consistency scopes, copies of facts, concurrency, observability. (Keyword conventions: see SKILL.md. Tags `(n)` name the deriving principle in `first-principles.md`; `(ledger)` its pattern-ledger entry.)

## Domain events

(1 — execution leaves receipts) Events MUST be past-tense business **facts** (*convention* on the tense; the derived part is that a receipt says what happened). Consumers: Inventory, Shipping, Notifications, Analytics.

```text
OrderApproved   OrderCancelled   OrderRefunded   InventoryReserved
```

You MUST NOT emit vague mutations (`OrderUpdated`, `EntityChanged`): a receipt that does not say what happened is not a receipt.

**Published events and `api/` are contracts** (13 — compatibility is a promise about sensitivity; ledger: stable versioned contract). Payload changes SHOULD be additive; a breaking change gets a new event version rather than a mutated old one; consumers SHOULD tolerate unknown fields. A consumer's proof that it handles `OrderApproved` MUST survive the producer's evolution, or the producer has changed the contract.

## Direct call vs. event

(11, 5) You SHOULD use a **direct call** when: same transaction, same invariant, or immediate (strong) consistency — the facts belong to one consistency scope, and an event would split it.
You SHOULD use an **event** when: another module merely reacts, eventual consistency is acceptable, and coupling should drop.

You SHOULD decide the consistency scope first (11), then coupling (5). Choosing an event for decoupling's sake where one invariant spans both sides breaks the invariant quietly; the violation merely has not been observed yet.

## Consistency model

(11) Every interaction MUST declare its consistency requirement (in the module README, and an ADR where it matters).

```text
Order creation         → Strong
Inventory reservation  → Strong
Email notification     → Eventual
Analytics update       → Eventual
```

The scope is exactly as large as its invariants demand. Facts an invariant binds together MUST change in one act (a transaction, one aggregate); facts no invariant binds MUST NOT be forced into one scope for storage or module convenience — indivisibility is the most expensive guarantee an environment sells, priced in serialization, contention, and coupled availability.

**Across scopes, agreement is a process, not a state.** An interaction declared Eventual MUST state its convergence path, and MUST treat the window of disagreement as a real, representable situation. A cross-module change that can fail midway MUST model its intermediate states, each with a path forward or back (a saga / process manager is one implementation — ledger); unmodeled, they are corruption pending discovery.

**A reader spanning scopes sees a moment, not a truth.** A read model, projection, or aggregation endpoint composing facts from several modules MUST tolerate their skew or state its staleness. It MUST NOT present the composite as if it had been observed within one scope.

Any handler crossing an eventual boundary (events, queues, retries) MUST be idempotent — see `domain-modeling.md`.

## Dual writes and the outbox

(11, 10, 1; ledger: outbox) When a state change and an event publish must both happen and the store and the bus are separate scopes, no single act can bind them. You MUST NOT commit-then-publish or publish-then-commit and call it atomic. Either record the pending publish durably in the same transaction as the state change and publish from that record (outbox, with an idempotent consumer), or decide explicitly that loss or duplication of the notification is acceptable and write that decision down. The outbox is earned ONLY when at-least-once delivery is actually required.

## Copies of facts

(6 — a redundant representation is a standing coherence obligation; 2) A cache, read model, denormalized column, or replicated lookup is a second copy of a fact, and it reintroduces the divergence single ownership designed away. It MAY exist ONLY with: a named authoritative home; a stated staleness bound or invalidation rule; and a measured need — latency, locality, or availability the home cannot provide. A copy with no stated staleness is a cache that lies. The home stays the only writer; the copy is read-only and subordinate.

## Concurrency & cancellation

**Cancellation is control flow, not an error case** (12, 10; ledger: cancellation propagation). Long-running or externally triggered work MUST propagate cancellation: when a request or job is abandoned, its child operations MUST be cancelled and its resources released. Thread the cancellation signal (Rust `CancellationToken`, Go `context.Context`, JS `AbortSignal`) exactly as correlation IDs are threaded. Orphaned work still running after its caller is gone is a defect: every spawned task MUST be owned by the lifetime that started it (structured concurrency — see State ownership in `structure-and-boundaries.md`). "Stopped partway" is a first-class outcome (10): a cancelled operation MUST leave state consistent — partial effects MUST be compensated or safely retryable (see idempotency in `domain-modeling.md`).

**Independent work MAY run concurrently, and if it does it MUST be bounded** (10 — bound the unbounded). Running N independent operations in parallel is a performance choice the framework does not price (§The limits of the framework itself); the bound is not optional. Unbounded fan-out against a shared resource (connection pool, third-party API) MUST NOT be used: it converts a latency win into an outage.

**Retries, bounds, and backpressure** (10, 9; ledger: retry under policy, backpressure / bounded queues, circuit breaker). Retries MUST be centralized under a stated policy — attempts, backoff, deadline — not scattered loops, and MUST target only infrastructure errors (see Error taxonomy in `domain-modeling.md`). Every queue, wait, and concurrent demand MUST have an explicit bound; an implicit one fails catastrophically. When production exceeds consumption, overload MUST propagate backward to the source (bounded queues, rejection, backpressure) rather than pool in the middle. A circuit breaker is earned ONLY under its premises: an external dependency, repeatedly failing, where attempts are costly and the failure is plausibly temporary.

**Scatter-gather** is the common shape of an aggregation endpoint:

```text
        ┌→ service A ┐
request ├→ service B ├→ gather → result
        └→ service C ┘
```

Where it is used, you MUST declare per-branch failure behavior (9): which branches are required, which MAY degrade to a partial result, and the deadline for the whole gather (10). A gather with no timeout is permanently as slow as its slowest branch. The gathered result composes facts observed at different instants (11): declare what the composite means when a branch is missing or stale.

## Observability

(1 — execution leaves receipts; 9 — a failure's audience includes the future) Important workflows MUST be reconstructable. Emit milestones (`OrderCreated`, `OrderApproved`, `InventoryReserved`, `PaymentCaptured`) with:

- **Structured logging** (machine-parseable fields) — MUST.
- **Correlation IDs** threaded through the whole workflow, across modules and async hops — MUST.
- **Traceability** — the workflow path MUST be recoverable.
- **Event visibility** — emitted facts MUST be recorded.

You MUST be able to reconstruct exactly what happened to one order, in order, from telemetry alone.

**Promised observations, not incidental ones** (1 vs 5). Emit for a named audience — operators, investigators, auditors — and treat those emissions as contracts. Everything else a module lets outsiders observe (timing, ordering, log wording, internal error detail) will be depended upon once it is stable (5 — the observable surface is the real interface), so minimize incidental observables and never let a log line become an integration point.

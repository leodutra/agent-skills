# Edge Case & Security Checklists

A filter, not a template: walk it, keep what changes observable behavior for this feature, drop the rest. A spec that answers every line below is over-specified. For each entry kept, state the observable outcome — not that the case "is handled".

## Edge Cases

- authorization / authentication failures
- missing resources
- invalid state for the operation
- duplicate requests / idempotency
- concurrent requests / race conditions
- retries and partial failure
- timeouts
- stale data / optimistic concurrency
- boundary dates and times
- timezone behavior, and which clock is authoritative (server, client, stored business time)
- empty data
- large inputs
- malformed inputs
- permission changes mid-flow
- external dependency failure
- records predating the rule — do they satisfy it, and what happens when one is acted on?

## Security

- authentication
- authorization
- ownership checks
- roles
- tenant isolation
- sensitive data handling
- retention and deletion semantics — does "delete" mean gone, hidden, or anonymized, and what do dependent features observe afterwards?
- auditability
- input validation
- abuse prevention (rate limits, enumeration)
- data exposure in responses and errors

Security requirements that affect observable behavior must be explicit in the specification.

## Pairing with adversarial review

Two questions after the walk. Both answers are defects — the first is over-specification, the second is the ambiguity the spec exists to remove.

- Which entry did I keep that traces to no stated intent or constraint?
- Which entry did I drop that a competent implementer would have to guess about?

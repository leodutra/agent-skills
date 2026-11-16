Each `.await` can cancel. A future dropped there MUST NOT break a domain invariant or silently lose
progress the application needs; where an operation can leave a partial effect (a partial write, a
charge without its record), the caller preserves, recovers, compensates or explicitly accepts it.

Question: can cancellation at an `.await` in this code (a `select!` branch losing, a dropped future)
break an invariant or silently lose needed progress, without the code preserving, recovering,
compensating or explicitly accepting it?

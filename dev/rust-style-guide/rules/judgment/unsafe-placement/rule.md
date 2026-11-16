- `unsafe` only where safe code can't do the job, and the crate says why (a measurement when the
  reason is speed): behind a safe API, in a module or crate of its own, never in domain code.
- A function is safe only if no argument causes undefined behavior; a condition only the caller can
  guarantee keeps it an `unsafe fn`, its contract under `# Safety`.
- A `// SAFETY:` comment states the invariant its block relies on.

Question: does this code break any of these rules?

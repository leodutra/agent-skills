- User input, CLI arguments included, is an error with a usage message and exit code, never
  `expect()`ed or silently replaced.
- Input-dependent indexing MUST use `get`/`get_mut` and handle `None`, or check bounds first.
- A poisoned lock's data is never read again; the poisoning is an error. A lock that doesn't poison
  (tokio, `parking_lot`) leaves no flag, so code holding it MUST NOT panic.
- Allowed: rebuilding a poisoned lock's whole value, then `clear_poison`, under a reasoned
  `#[expect(clippy::disallowed_methods, reason = "…")]`.

Question: does this code break any of these rules?

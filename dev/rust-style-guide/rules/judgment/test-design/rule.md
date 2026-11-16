- No second example of a pinned rule; no tests of derives, getters or compiler guarantees.
- A law gets a property test instead of examples; where `Display` is the type's canonical text, a
  round-trip one MUST pin it over generated values.
- Every forbidden transition the types allow is tested.
- Setup uses `expect("why it holds")` (`unwrap()` where obvious); the behavior under test is
  asserted on its `Result`, never unwrapped.

Question: does this code break any of these rules?

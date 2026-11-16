A bug is neither an error variant nor a silent fallback (`unwrap_or_default()` over a state that
can't happen): make the state unrepresentable; where types can't, a reasoned
`#[expect(clippy::unreachable, …)]` marks the claim. Illegal states MUST be unrepresentable: fields
that exist only together are one variant's data.

Question: does this code handle a state its own types or constructors rule out with an error variant
or a silent fallback, instead of making that state unrepresentable?

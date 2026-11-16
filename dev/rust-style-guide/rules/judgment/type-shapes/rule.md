- Illegal states MUST be unrepresentable. State from storage or the wire is an enum, not typestate.
- One meaning per `Option`; sentinels (`""`, `0`, `-1`) MUST NOT stand for absence.
- A closed set is an enum, not a refinement over a string.
- More than one field means named fields: no tuples or tuple structs beyond a newtype.
- Variant fields are public, so fields sharing an invariant MUST sit in a refinement the variant
  wraps.

Question: does this code break any of these rules?

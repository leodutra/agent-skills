- Derive `Debug, Clone, PartialEq`, and `Copy`, `Eq`, `Hash`, `Ord` wherever the fields allow and
  the contract holds. Hand-write a trait only where the derived behavior is wrong for the type,
  never to spell out what the derive does, and then hand-write the traits that must agree with it.
- Derived `Ord` follows declaration order: declare variants and fields in the domain's order; an
  order one caller needs is a `sort_by_key` there.
- `Eq` adds reflexivity: derive it, and hand-write it only where the invariant guarantees it (a
  finite-float refinement), never over a `PartialEq` that breaks it (`f32`/`f64` aren't `Eq`).
  Where identity needs `Eq` and a field can't give it, fix the model; a value meant to follow IEEE
  754 keeps `PartialEq` alone.
- A secret hand-writes a redacted `Debug`, with no `Display` and no `Serialize`.

Question: does this code break any of these rules?

- At every boundary, data is parsed into domain types before domain logic; from then on the type is
  the proof. The boundary type is itself built from domain types: a request, row or DTO field whose
  value has a refinement or tag MUST use it, so deserializing runs its constructor, and no primitive
  travels past the boundary. A separate DTO, still built from domain types, exists only when the
  wire's shape differs, or as the mirror serde needs to reach a cross-field constructor.
- Code MUST NOT re-check the invariant; functions MUST take the refinement, never its primitive. A
  yes/no check (`is_valid_x(&str) -> bool`, `validate(&self)` over public fields) MUST become the
  constructor.
- A database decoder decodes the inner type, then calls `try_from`.
- clap: a refinement parses through `FromStr`, a closed set through `ValueEnum`; a custom
  `value_parser` needs a stated reason.

Question: does this code break any of these rules?

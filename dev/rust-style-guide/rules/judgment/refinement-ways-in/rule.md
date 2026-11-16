- No value of the type exists that breaks its invariant. One validation, and every way in runs it:
  `FromStr` (its output printed back by `Display`), text and primitive `TryFrom`, serde, database
  decoders.
- An inherent fallible constructor MUST be `try_new`, returning `Result`, never `Option`.
- Normalize first (trim, canonical case) so `Eq`/`Hash`/`Ord` compare canonical values, keeping
  every distinction the domain keeps (an email lowercases its domain, not its local part).
- `Borrow<str>` only if the type's `Eq`, `Ord` and `Hash` match `str`'s for every borrowed value
  and lookup key. Normalization at construction is fine; normalization during comparison is not
  (a type comparing case-insensitively, or by any rule other than its stored text's, has none).

Question: does this code break any of these rules?

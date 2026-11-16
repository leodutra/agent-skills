- No value of the type exists that breaks its invariant. One validation, and every way in runs it:
  `FromStr` (its output printed back by `Display`), text and primitive `TryFrom`, serde, database
  decoders.
- An inherent fallible constructor MUST be `try_new`, returning `Result`, never `Option`.
- Normalize first (trim, canonical case) so `Eq`/`Hash`/`Ord` compare canonical values, keeping
  every distinction the domain keeps (an email lowercases its domain, not its local part).
- `Borrow<str>` only if `Eq`, `Hash` and `Ord` agree with `str`'s.

Question: does this code break any of these rules?

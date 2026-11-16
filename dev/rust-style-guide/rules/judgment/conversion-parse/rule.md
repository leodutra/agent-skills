- **Conversion**: one typed value becomes unambiguously the same value in another type, with nothing
  lost, rounded or chosen. A constructor taking several values is not a conversion.
- **Parsing**: interpreting a text or byte representation by a grammar or encoding. Complete text
  with one unambiguous interpretation MUST parse through `FromStr`. `TryFrom<&str>` and
  `TryFrom<String>` MAY sit beside it with the same semantics, never replace it. Complete bytes with
  one context-free interpretation MAY use `TryFrom<&[u8]>`; otherwise (byte order, version, policy,
  borrowing, streaming) a named decoder.
- A closed set's `ValueEnum` (clap) or `rename_all` (serde) names are its canonical text; code that
  parses that text itself does so in a `FromStr` that accepts the same names.

Question: does this code break any of these rules?

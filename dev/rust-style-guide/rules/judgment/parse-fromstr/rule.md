**Parsing**: interpreting a text or byte representation by a grammar or encoding. Complete text with
one unambiguous interpretation as an owned value MUST parse through `FromStr`, whatever else the type
offers; it may accept several spellings, while `Display` prints one. `TryFrom<&str>` and
`TryFrom<String>` MAY sit beside it with the same semantics, never replace it. A parse that extracts
(part of the input, or many values) is a named function that says what it takes (`parse_query`), or
a collection type with `FromStr` when the whole input is one collection. A parse that chooses among
formats, policies or interpretations is a named function that says the choice (`from_json`).

Question: does this code parse complete text into an owned value by anything other than `FromStr`
(a `TryFrom<&str>` or a named function in its place), where `FromStr` is missing?

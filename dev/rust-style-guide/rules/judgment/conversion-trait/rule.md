For an unambiguous conversion or a complete text parse, a name MUST NOT replace the trait
(`Foo::from_u16` with no `TryFrom<u16>` is a defect); it MAY sit beside it. Where the trait would
hide a loss, a rounding, an ambiguity or a policy, the named function says so in its doc comment;
merely describing the input is not a reason. `From` when it can't fail, `TryFrom` when it fails
rather than lose anything (into a refinement, narrowing a number).

Question: does this code offer an unambiguous conversion only through a named function, with no
`From`/`TryFrom` implementation for it?

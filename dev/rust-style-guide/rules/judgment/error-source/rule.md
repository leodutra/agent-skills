Library errors are typed (`thiserror` enum, or a unit struct for one failure) and implement
`Error + Send + Sync + 'static`, with typed context (`InvalidTransition { from, to }`); `String`,
`&str`, `()` and `Box<dyn Error>` MUST NOT be the error or carry its context. A domain or library API
MUST NOT return a dependency's error raw: wrap it in a variant of your own, kept as `#[source]`.
Derive `Clone, PartialEq, Eq`, and `Copy` where the fields allow, unless a cause can't
(`io::Error`), so tests assert variants.

Question: does an error in this code break this rule (a `String`/`&str`/`()`/`Box<dyn Error>` error
or context, a cause flattened to text, a dependency's error returned raw, or `Clone`/`PartialEq`/`Eq`
missing where every cause has them)?

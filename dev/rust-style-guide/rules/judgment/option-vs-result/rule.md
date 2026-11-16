`Option` is absence, `Result` failure; neither stands in for the other (no `.ok()` dropping an
error). A fallible lookup returns `Result<Option<T>, E>` (`Ok(None)` not found, `Err` the store
failing); an operation that needs the value makes absence an error variant; a lookup that can't fail
returns `Option`. One meaning per `Option`; sentinels (`""`, `0`, `-1`) MUST NOT stand for absence.

Question: does this code let `Option` and `Result` stand in for each other (an error turned into
`None` or `Ok(None)`, absence reported as an error where it is a normal outcome, or a sentinel for
absence)?

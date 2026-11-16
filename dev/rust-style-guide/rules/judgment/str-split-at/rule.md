Slice a `str` only at char boundaries (`split_once`, `char_indices`, `get(a..b)`), never
`split_at`/`&s[a..b]` at an offset input can move. Input-dependent indexing MUST use `get`/`get_mut`
and handle `None`, or check bounds first.

Question: does this code split, slice or index a `str` (or a slice) at an offset that input can move,
where it can panic?

Match your own enums exhaustively: no `_ =>`, no `#[non_exhaustive]` (it forces `_` arms on the
workspace's other crates; only a crate published to users you don't rebuild uses it).

Question: does this code put `#[non_exhaustive]` on a type in a crate whose users are rebuilt with it
(the same workspace), or match its own enum with a wildcard?

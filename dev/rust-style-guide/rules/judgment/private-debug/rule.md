Derive `Debug, Clone, PartialEq`, and `Copy`, `Eq`, `Hash`, `Ord` wherever the fields allow and the
contract holds. Every type provides `Debug`, private ones included (the `missing_debug_implementations`
lint sees only public types); only a secret hand-writes a redacted `Debug`.

Question: does a type in this code, public or private, lack `Debug` (or a derive its fields allow
and its contract supports)?

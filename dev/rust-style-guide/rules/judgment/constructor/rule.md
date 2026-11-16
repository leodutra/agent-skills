An inherent fallible constructor MUST be `try_new`, returning `Result`, never `Option`; `new` can't
fail. Other names follow C-CTOR: an I/O resource's domain verb (`open`, `connect`, `bind`), `with_*`
for a secondary constructor, `from_*` only for a parse that chooses; a conversion is the trait, and
a name only sits beside it. Its error holds only the failures it can produce: a unit struct for one,
an enum for several. Constructors MUST NOT share an enum that either can't fully produce.

Question: does a constructor in this code break this rule (its name, its return type, or an error
type holding failures it can't produce)?

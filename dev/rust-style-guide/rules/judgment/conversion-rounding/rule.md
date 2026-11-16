**Conversion**: one typed value becomes unambiguously the same value in another type, with nothing
lost, rounded or chosen; wrapping a primitive without a check (a tag) counts. `From` when it can't
fail, `TryFrom` when it fails rather than lose anything. A tag's `From` is fine where the two types
make the meaning obvious (`From<u64> for UserId`, `From<u32> for Grams`). A unit change that rounds
(grams to whole ounces) is a named method (`Grams::to_whole_ounces`). A conversion that would
surprise a reader of `.into()` is never a trait: a named function says what it does.

Question: does this code implement `From`/`TryFrom` (or `Into`) for something that is not such a
conversion, e.g. one that rounds, loses information or chooses?

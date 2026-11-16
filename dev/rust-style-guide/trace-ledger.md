# rust-style-guide trace ledger

One row per ID in `skills/rust-style-guide/references/fundamentals.md`, checked by `trace.py`.
Home `lint` names lints.toml lints and clippy.toml entries; `skill` quotes SKILL.md (short fragments,
so rewording elsewhere in a bullet doesn't break them); `lint+skill` is a lint-held rule SKILL.md
restates, and the note says why the model needs it before linting. `;` separates items.

| ID | Home | Holds | Note |
| --- | --- | --- | --- |
| M1 | skill | "**When rules pull apart**, the first wins" | precedence order |
| M2 | skill | "A documented project decision"; "A documented project requirement" | |
| M3 | skill | "more specific guidance for the code at hand" | |
| M4 | skill | "Performance overrides a convention only with" | |
| M5 | skill | "`MUST`/`SHOULD`/`MAY` are literal" | |
| M6 | skill | "**Proportionality**: a newtype" | |
| M7 | skill | "What clippy can check, clippy checks"; "if CI runs them, else report it too" | |
| M8 | skill | "drop anything [Allowed](#allowed), not even a nit" | |
| M9 | skill | "A lint misfire gets" | |
| M10 | skill | "`review [target]` → **Review**"; "`audit` → **Review** of the whole codebase"; "`lint [target]` (code or crates"; "Other text, or none → the task" | |
| M11 | skill | "Lints: paste [assets/lints.toml](assets/lints.toml)"; "Types before functions"; "Done: `cargo check`" | |
| M12 | skill | "**Domain code**: library and domain logic" | |
| L1 | lint | level deny | every lint deny, unsafe_code forbid |
| L2 | lint | clippy::allow_attributes; clippy::allow_attributes_without_reason | |
| L3 | lint | config avoid-breaking-exported-api | |
| L4 | lint | clippy::infallible_try_from; clippy::result_unit_err; clippy::await_holding_lock; clippy::await_holding_refcell_ref; clippy::disallowed_types; clippy::disallowed_methods; clippy::missing_safety_doc; clippy::derived_hash_with_manual_eq; clippy::derive_ord_xor_partial_ord | clippy defaults, listed |
| L5 | lint | unsafe_code | |
| L6 | lint | clippy::undocumented_unsafe_blocks | presence; the comment's content is S4 |
| L7 | lint | clippy::multiple_unsafe_ops_per_block | |
| L8 | lint | unsafe_op_in_unsafe_fn | |
| L9 | lint | clippy::missing_safety_doc | presence; the contract's content is S3 |
| L10 | lint | clippy::partial_pub_fields | |
| L11 | lint | missing_debug_implementations | public types; private ones are S12 |
| L12 | lint | clippy::derive_partial_eq_without_eq | |
| L13 | lint | clippy::derivable_impls | |
| L14 | lint | clippy::expl_impl_clone_on_copy | |
| L15 | lint | clippy::derived_hash_with_manual_eq; clippy::derive_ord_xor_partial_ord | |
| S1 | skill | "`unsafe` only where safe code can't do the job" | |
| S2 | skill | "behind a safe API, in a module or crate of its own" | |
| S3 | skill | "A function is safe only if no argument causes undefined behavior" | |
| S4 | skill | "states the invariant its block relies on" | |
| S5 | skill | "At every boundary, data is parsed into domain types"; "Code MUST NOT re-check the invariant"; "**Boundary**: anywhere data from outside" | |
| S6 | skill | "MUST become the constructor" | |
| S7 | skill | "The boundary type is itself built from domain types"; "A cross-field rule lives there" | |
| S8 | skill | "A value with an invariant, or swappable with another" | |
| S9 | skill | "A tag's field is `pub`"; "**Tag**: a newtype with no invariant"; "A tag's `pub` field, `#[serde(transparent)]`" | the Allowed entry too |
| S10 | skill | "never `impl Into<Newtype>`" | |
| S11 | skill | "A refinement's fields MUST be private" | |
| S12 | skill | "private type missing `Debug`" | |
| S13 | skill | "A secret hand-writes a redacted `Debug`" | |
| S14 | skill | "`Eq` adds reflexivity" | |
| S15 | skill | "Hand-write a trait only where" | |
| S16 | skill | "`Default` only if the default is valid" | |
| S17 | skill | "Derived `Ord` follows declaration order" | |
| S18 | skill | "Derive `Debug, Clone, PartialEq`, and `Copy`" | |
| S19 | skill | "a value meant to follow IEEE 754" | |
| S20 | skill | "a `try_*` method returning `Result`, never an operator" | e.g. `Km::try_add`; `Add` can't return an error |
| S21 | skill | "One validation, and every way in runs it" | |
| S22 | skill | "An inherent fallible constructor MUST be `try_new`"; "`new` returning `Result`" | |
| S23 | skill | "Other names follow C-CTOR"; "Instead of `try_new`: an I/O resource's fallible" | `from_*` also names a unit (C9) |
| S24 | skill | "returning `Result`, never `Option`" | |
| S25 | skill | "Its error holds only the failures it can produce"; "A unit-struct error for a constructor with one failure" | |
| S26 | skill | "its output printed back by `Display`"; "`default_value_t = CONST` relies on" | |
| S27 | skill | "Normalize first (trim, canonical case)" | |
| S28 | skill | "`Borrow<str>` only if those agree" | |
| S29 | skill | "No value of the type exists that breaks its invariant" | |
| S30 | skill | "No `Deref`/`DerefMut`, no `&mut` to the inner value" | |
| S31 | skill | "serde: `#[serde(try_from"; "skips the constructor and MUST NOT be used" | |
| S32 | skill | "`Decode`/`FromSql` decodes the inner type" | |
| S33 | skill | "clap: a refinement parses through `FromStr`" | |
| S34 | skill | "`literal` calls `try_new`, never builds `Self`"; "`literal`'s panic in `const` items" | |
| S35 | skill | "**Conversion**: one typed value becomes unambiguously" | |
| S36 | skill | "a name MUST NOT replace the trait"; "An unambiguous conversion or complete text parse without its trait" | |
| S37 | skill | "A conversion that would surprise a reader" | |
| S38 | skill | "A primitive whose type doesn't carry its unit is ambiguous" | |
| S39 | skill | "**Parsing**: interpreting a text or byte representation" | |
| S40 | skill | "MUST parse through `FromStr`" | |
| S41 | skill | "names are its canonical text" | |
| S42 | skill | "MAY sit beside it with the same semantics"; "A type that borrows its input uses" | |
| S43 | skill | "Complete bytes with one context-free interpretation" | |
| S44 | skill | "A parse that extracts"; "A parse that chooses among formats"; "A named parser or decoder for a parse that extracts or chooses" | |
| L16 | lint | clippy::infallible_try_from | |
| L17 | lint | clippy::unnecessary_wraps | |

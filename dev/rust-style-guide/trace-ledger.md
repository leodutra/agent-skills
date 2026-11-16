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
| M7 | skill | "What clippy can check, clippy checks"; "if CI runs them, else report it too"; "Review every other rule, and what slips past" | |
| M8 | skill | "drop anything [Allowed](#allowed), not even a nit"; "Not defects, not even nits" | |
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
| S35 | skill | "**Conversion**: one typed value becomes unambiguously"; "what the source is decides" | |
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
| S45 | skill | "Illegal states MUST be unrepresentable" | |
| S46 | skill | "One meaning per `Option`" | |
| S47 | skill | "MUST NOT stand for absence" | |
| S48 | skill | "A closed set is an enum, not a refinement over a string" | |
| S49 | skill | "State from storage or the wire is an enum" | |
| S50 | skill | "Variant fields are public, so fields sharing" | |
| S51 | skill | "More than one field means named fields" | |
| S52 | skill | "`Option` is absence, `Result` failure" | |
| S53 | skill | "A fallible lookup returns"; "a lookup that can't fail returns `Option`"; "`Result<Option<T>, E>` from a lookup" | |
| S54 | skill | "A `Result` dropped where dropping is right" | |
| S55 | skill | "no `.ok()` dropping an error"; "`.ok()` hiding an error" | |
| S56 | skill | "bound to `_name` or `drop`ped" | |
| S57 | skill | "Library errors are typed" | |
| S58 | skill | "private `Result<_, ()>`" | |
| S59 | skill | "MUST NOT return a dependency's error raw" | |
| S60 | skill | "names the cause, loses its type" | |
| S61 | skill | "`anyhow`/`eyre` only where errors only get printed"; "`anyhow`/`eyre` in a binary's `main` and CLI commands" | C1: no infrastructure libraries; tests of a library stay under the ban |
| S62 | skill | "Derive `Clone, PartialEq, Eq` (reflexive"; "An error lacking `Clone`/`PartialEq`/`Eq`" | |
| S63 | skill | "Messages: lowercase, no trailing period" | |
| L18 | lint | clippy::struct_excessive_bools; clippy::fn_params_excessive_bools | |
| L19 | lint | clippy::option_option | |
| L20 | lint | clippy::unused_result_ok; clippy::let_underscore_must_use | |
| L21 | lint | clippy::result_unit_err | |
| L22 | lint | clippy::map_err_ignore | |
| L23 | lint | disallowed-types anyhow::Error; disallowed-types anyhow::Result; disallowed-types eyre::Report; disallowed-types eyre::Result | |
| L24 | lint+skill | clippy::unwrap_used; clippy::expect_used; clippy::panic; "MUST NOT appear outside tests" | totality shapes signatures and error types; learned from clippy, the API gets redesigned |
| S64 | skill | "Functions are total" | |
| S65 | skill | "except `expect()` with a clear message"; "`main.rs` `expect()` with a clear message" | |
| S66 | skill | "User input, CLI arguments included, is an error" | |
| L25 | lint | clippy::todo; clippy::unimplemented | tests included (C2) |
| L26 | lint | clippy::unreachable | tests included (C2) |
| S67 | skill | "A bug is neither an error variant nor a silent fallback" | |
| L27 | lint+skill | disallowed-methods std::sync::PoisonError::into_inner; disallowed-methods std::sync::PoisonError::get_ref; disallowed-methods std::sync::PoisonError::get_mut; "its data is never read again" | the poisoning becomes an error variant: error-type design |
| S68 | skill | "Rebuilding a poisoned lock's whole value" | C7 |
| S69 | skill | "A lock that doesn't poison" | |
| L28 | lint | disallowed-methods std::panic::catch_unwind | |
| L29 | lint+skill | disallowed-methods std::process::abort; clippy::exit; "Library code MUST NOT call `process::exit`/`abort`" | returning an error instead of exiting changes the signature |
| L30 | lint+skill | clippy::cast_possible_truncation; clippy::cast_sign_loss; clippy::cast_possible_wrap; "never `as`" | `TryFrom` returns `Result`, so a narrowing conversion changes the signature |
| L31 | lint | clippy::string_slice | |
| S70 | skill | "Slice a `str` only at char boundaries"; "`split_at` on `str`" | |
| S71 | skill | "Input-dependent indexing MUST use" | C10: or check bounds first |
| S72 | skill | "Money and quantity arithmetic that can overflow"; "overflowing arithmetic" | |
| S73 | skill | "check a possibly-zero divisor" | |
| S74 | skill | "Money: integer minor units or a decimal type" | |
| L32 | lint | clippy::dbg_macro; clippy::print_stdout; clippy::print_stderr | a binary prints under a reasoned #[expect] (C6) |
| L33 | lint+skill | config allow-unwrap-in-tests; config allow-expect-in-tests; config allow-panic-in-tests; config allow-dbg-in-tests; config allow-print-in-tests; "Test allowances cover `#[test]`"; "`unwrap()`, `expect()`, `panic!`, `dbg!` and printing in" | a `tests/` helper written to unwrap must be rewritten to return `Result` (C3) |
| L34 | lint | clippy::wildcard_enum_match_arm; clippy::match_wildcard_for_single_variants | SKILL.md's "no `_ =>`" dropped: the fix is local |
| S75 | skill | "No `#[non_exhaustive]` on your own types"; "`#[non_exhaustive]` in a crate published" | structs too |
| L35 | lint | clippy::needless_pass_by_value | |
| L36 | lint | clippy::ref_option | |
| L37 | lint | clippy::redundant_clone | |
| S76 | skill | "Borrow inputs" | |
| S77 | skill | "to quiet the borrow checker" | |
| S78 | skill | "Shared ownership (`Rc`/`Arc`) only where" | |
| L38 | lint+skill | disallowed-types std::cell::Cell; disallowed-types std::cell::RefCell; disallowed-types std::sync::Mutex; disallowed-types std::sync::RwLock; "no interior mutability"; "the clock, randomness and locks outside" | a type mutated through `&self` is redesigned to `&mut self`, with the caller sharing |
| S79 | skill | "atomics, `OnceCell`, other interior mutability" | |
| L39 | lint+skill | disallowed-methods std::time::SystemTime::now; disallowed-methods std::time::Instant::now; disallowed-methods chrono::Utc::now; disallowed-methods rand::random; disallowed-methods rand::rng; disallowed-methods rand::thread_rng; disallowed-methods uuid::Uuid::new_v4; disallowed-methods uuid::Uuid::now_v7; "time and randomness are parameters" | time and randomness become parameters: a signature change through every caller |
| S80 | skill | "Time or randomness missing from `clippy.toml`" | |
| L40 | lint | clippy::iter_over_hash_type | |
| S81 | skill | "depend on `HashMap`/`HashSet` order"; "hash iterator chains" | |
| L41 | lint+skill | clippy::disallowed_macros; disallowed-macros ctor::ctor; disallowed-macros dtor::dtor; "No code runs before or after `main`" | startup wiring moves into `main`: a structural change (C5: teardown may be the owner's `Drop`) |
| L42 | lint | clippy::await_holding_lock; clippy::await_holding_refcell_ref | SKILL.md's restatement dropped: scoping the guard is a local fix |
| L43 | lint | clippy::future_not_send | |
| S82 | skill | "A trait whose futures are spawned multithreaded" | |
| S83 | skill | "A non-`Send` future deliberately run only" | |
| L44 | lint | clippy::let_underscore_future | |
| S84 | skill | "A future MUST be awaited, returned or spawned" | |
| S85 | skill | "No blocking on the runtime" | |
| S86 | skill | "Each `.await` can cancel" | |
| L45 | lint | clippy::needless_for_each | |
| S87 | skill | "A name says what the thing does" | |
| S88 | skill | "Accessors follow std" | |
| S89 | skill | "A trait exists only for a real abstraction need"; "An extension trait (`…Ext`) with a single implementation" | |
| S90 | skill | "An operator means its mathematical or logical operation" | |
| S91 | skill | "Macros last" | |
| S96 | skill | "Unused dependencies" | `unused_crate_dependencies` flags per target: too noisy |
| L46 | lint | clippy::assertions_on_result_states | |
| S92 | skill | "Per constructor: one accepted input"; "a rejection test asserting its error" | |
| S93 | skill | "No second example of a pinned rule" | |
| S94 | skill | "A law gets a property test" | |
| S95 | skill | "Every forbidden transition the types allow is tested" | |
| L47 | lint | clippy::wrong_self_convention; clippy::should_implement_trait; clippy::len_without_is_empty; clippy::new_without_default; clippy::ptr_arg; clippy::borrowed_box | clippy defaults fundamentals relied on, now listed |
| L48 | lint | clippy::wildcard_imports | |
| L49 | lint | clippy::derive_partial_eq_without_eq | a published crate may drop it (comment in lints.toml) |
| L50 | lint | disallowed-types anyhow::Error; disallowed-types anyhow::Result; disallowed-types eyre::Report; disallowed-types eyre::Result; disallowed-methods chrono::Utc::now; disallowed-methods rand::random; disallowed-methods rand::rng; disallowed-methods rand::thread_rng; disallowed-methods uuid::Uuid::new_v4; disallowed-methods uuid::Uuid::now_v7; disallowed-macros ctor::ctor; disallowed-macros dtor::dtor | allow-invalid entries and per-crate omissions (clippy.toml comments) |
| S97 | skill | "the behavior under test is asserted on its `Result`" | setup `expect`s (`unwrap` where obvious) |

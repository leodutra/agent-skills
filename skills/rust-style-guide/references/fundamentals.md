# Why the Rust style guide says what it says

This file is for people. It gives the reason behind every rule in [SKILL.md](../SKILL.md) and every
entry in [`assets/lints.toml`](../assets/lints.toml) and [`assets/clippy.toml`](../assets/clippy.toml),
with examples. If a lint fired on your code, search this page for its name. Sections are grouped by
the problem they prevent. Each one gives the reason, then the lints that enforce it, then what
review has to check by hand.

## How this file, the lints and SKILL.md divide the work

- **This file is the source of truth.** Every rule lives here first, with its reason and examples,
  tagged with an ID in parentheses: `L` and a number for a rule the lints hold, `S` for one SKILL.md
  holds, `M` for a rule about applying the guide. Nothing exists in the lints or SKILL.md without a rule here.
- **The lints hold every rule a lint can hold.** They are deterministic, fast and cost no tokens, and
  they run on every compile, in CI and while fixing.
- **SKILL.md holds the rest**, in as few words as decide the behavior, without the reasons. It
  restates a lint-held rule only when code written without knowing it would need a redesign once
  the lint fires (totality, error types, API shape); a local fix (a glob import, a missing derive)
  is left to the lint. A rule a lint holds only in part is split: the lint takes its part, SKILL.md
  the rest.

**Checklist for any rule change:**

1. Write or update the rule here first: the reason, an example, and a new ID (never reuse one).
2. If a lint can hold it, add the lint to `lints.toml` or `clippy.toml` with a comment, plus a bad
   and a good sample that prove it fires.
3. Otherwise, or for the part a lint misses, state it in SKILL.md.
4. Restate a lint-held rule in SKILL.md only if skipping it means a redesign later.
5. Remove or change nothing in SKILL.md or the lints without changing its rule here.
6. In this repository, `dev/rust-style-guide/trace.py` checks steps 1 to 5 against its ledger.

## Two ideas underneath everything

The guide started in early 2026 as a prose document. It rested on two ideas, and every rule here
still follows from one of them.

1. **If it compiles, it's valid.** Put the rules in types, and the compiler checks them on every
   build, in every file, for free. A rule that lives only in a comment, a code review or someone's
   memory gets broken the first time nobody looks. Most of this guide is about moving a check from
   run time, or from a reviewer, into a type.
2. **Ownership is design.** Who owns a value, who borrows it and who consumes it isn't an
   implementation detail. Those choices are the API. A signature that takes `String` where `&str`
   would do, or that clones to dodge the borrow checker, is a design mistake, not a style nit.

In September 2026 the checks that a tool can make moved from prose to clippy and rustc lints.
Prose works only when someone reads it and follows it. A lint runs on every change, whoever wrote
it.

## The same ideas, inverted

Ask the opposite question: how would you write Rust that surely breaks in production? Each answer
is something this guide bans, so the list doubles as a check on a rule you're unsure about. If
dropping the rule lets one of these back in, the rule stays.

| To guarantee failure | The guide's answer |
| --- | --- |
| Check a value in one place and trust it everywhere else | The check is the constructor, and the type is the proof (sections 2 to 4) |
| Let a type hold states the domain forbids, and remember not to build them | The type can't hold them (section 5) |
| Report "missing" and "broken" the same way | `Option` for absence, `Result` for failure (section 6) |
| Throw away the cause of an error, or put it in a string | Typed errors that keep their source (section 7) |
| Hide a lossy or ambiguous conversion behind `.into()` | A trait impl only for an obvious conversion (section 4) |
| Crash on input you didn't expect | Total functions, no panics outside tests (section 8) |
| Turn a bug into a default value, so the data is wrong later | A bug is fixed in the types, never papered over (section 8) |
| Add an enum variant and let old matches swallow it | No `_ =>` on your own enums (section 9) |
| Clone until the borrow checker is quiet | Borrow unless ownership is needed (section 10) |
| Read the clock or a random number wherever it's handy | Time and randomness are parameters (section 11) |
| Block the runtime, or stop halfway through an effect | Async rules (section 12) |
| Leave the rule to the reviewer's memory | A `deny` lint, on every build (lint section) |
| Apply every rule everywhere, wrapping every value and abstracting every call | Proportionality: an abstraction pays for itself (next section) |

## When rules pull apart, and how much of them to apply

Good rules still conflict. A conversion rule says "implement `From`", and an obviousness rule says
"not if it surprises the caller". Without an order, two careful readers pick differently. So the
guide ranks them, and the first wins: memory and type safety, then domain invariants, then semantic
clarity, then std-trait interoperability, then simplicity, then performance, then style (M1). Safety and
invariants come first because a breach there corrupts data or memory, and no amount of clarity
repairs that. Clarity comes before conformity, because a trait impl that misleads is worse than a
named function that doesn't fit a pattern.

Two kinds of reason may override a convention, and both are written down. A documented project
requirement, such as a hard real-time deadline or a stable public API, can bend a convention, never
safety or an invariant (M2). It wins only on the point and in the scope it names, and it lives where
decisions are made and found (`CLAUDE.md`, an ADR, the project's docs). A code comment doesn't
count: it explains one spot, and nobody looks for a project's rules inside it. More specific
guidance for the code at hand, such as a framework's conventions or another loaded skill, wins the
same way, on its point only: it knows its context better than a general guide does (M3).
Performance can
override a convention only with evidence: a measurement or a stated system constraint, recorded
where the code deviates (M4). "This might be slow" is not evidence, and most of what the guide asks for
(newtypes, borrowing, enums) costs nothing at run time.

`MUST`, `SHOULD` and `MAY` in SKILL.md are literal, as in RFC 2119, so a reader takes them as
levels of obligation, not emphasis (M5).

**Proportionality** is the other half. Every abstraction here earns its place by doing a job: a
newtype enforces an invariant or stops two values being swapped, a trait serves a real abstraction
need, an error variant is a failure a caller can act on. Applied to a value with no
invariant and no confusable twin, the same tools only add names and indirection. So a newtype,
trait, error variant, layer or generic parameter exists only when it enforces an invariant,
prevents a real misuse, names a domain concept or measurably eases maintenance (M6). The rules say how
such a thing is built once it is needed, never that every value needs one. A guide that makes code
heavier than the problem has failed as surely as one that lets bugs through.

## How the lint configuration works

Five decisions shape the whole setup.

- **The machine checks what a machine can check.** You can't argue a lint out of a verdict, and it
  doesn't get tired. A reviewer, human or model, can be argued with and does get tired. So every
  rule that clippy or rustc can hold is handed to them, and review covers only the rest, when CI
  runs the lints; without CI, review reports lint findings too (M7).
- **A review checks every rule and reports each finding with its line, the rule, why and the
  fix**, a whole-codebase audit grouped by rule, most severe first. It drops anything on SKILL.md's
  Allowed list entirely, not even as a nit: reporting an allowed construct costs the author a
  decision the guide already made (M8).
- **Every Clippy lint is `deny`, not `warn`.** The rustc `unsafe_code` lint is `forbid` by default.
  Warnings pile up until nobody reads them. A lint that matters fails the build, and a lint that
  doesn't matter isn't on the list. Rustc's `missing_debug_implementations` is also `deny` (L1).
- **Exceptions are written down where they happen.** A lint is never turned off for a whole crate
  because one place needs an exception. That place gets `#[expect(clippy::name, reason = "…")]`,
  and the `reason` tells the next reader why. `expect`, unlike `allow`, fails once the lint stops
  firing, so a stale exception can't linger. `allow_attributes` bans a bare `#[allow]`, and
  `allow_attributes_without_reason` bans an exception with no `reason` (L2, M9).
- **Public signatures are linted like private ones** (`avoid-breaking-exported-api = false`).
  Clippy normally leaves public signatures alone so that it doesn't push a breaking release. In a
  workspace you rebuild, changing a public signature is a refactor, not a release. A crate published
  to outside users drops this line, and for the same reason it may use `#[non_exhaustive]` (see
  section 9) (L3).
- **Default lints are still listed.** Nine entries (`infallible_try_from`, `result_unit_err`,
  `await_holding_lock`, `await_holding_refcell_ref`, `disallowed_types`, `disallowed_methods`,
  `missing_safety_doc`, `derived_hash_with_manual_eq`, `derive_ord_xor_partial_ord`) are already on
  in clippy by default. They are listed anyway, so that the file states every rule it holds and
  raises them to `deny` (L4).

## Applying SKILL.md

SKILL.md has four entry points: `review` checks a diff or target against every rule, `audit` does
the same for a whole codebase, `lint` installs the lint set where it's missing and fixes what it
finds, and anything else is a task to write (M10). Writing starts with the lint set, so every line
is checked as it's written. Then types come before functions, because signatures are built from
them: a refinement per value with an invariant, an enum per set of states, an error type per set of
failures. A task is done when `cargo check`, `cargo fmt --check`, `cargo clippy --all-targets -- -D
warnings` and `cargo test` pass (M11). **Domain code** is library and domain logic. A binary's
`main` and infrastructure (adapters, wiring) are not, and some rules (the clock, randomness, locks,
`anyhow`) apply only to domain code (M12).

## 1. Memory safety stays the compiler's job

| Lint | Catches |
| --- | --- |
| `unsafe_code = "forbid"` | any `unsafe` |
| `undocumented_unsafe_blocks` | an `unsafe` block with no `// SAFETY:` comment |
| `multiple_unsafe_ops_per_block` | an `unsafe` block holding more than one unsafe operation |
| `unsafe_op_in_unsafe_fn` | an unsafe operation in an `unsafe fn` body outside an `unsafe` block |
| `missing_safety_doc` (clippy default) | a public `unsafe fn` without a `# Safety` section |

Rust's main promise is that safe code can't corrupt memory. An `unsafe` block is a proof the
compiler can't check, and domain or backend code almost never needs one. `forbid` is stricter than
`deny`: no attribute in the code can lift it, so nobody quietly opts out. A crate that really needs
`unsafe`, such as an FFI wrapper, lowers this one lint to `deny` and puts an
`#[expect(unsafe_code, reason = "…")]` on each item (L5). Then the `// SAFETY:` comment states the
invariant the block relies on, so a reviewer can check the proof the compiler couldn't (L6, S4).

Where `unsafe` is needed, it is fenced, so the unchecked proof stays small enough to review:

- **Only where safe code can't do the job**, and the crate says why. When the reason is speed, a
  benchmark shows it: performance overrides a convention only with a measurement (precedence,
  above), and an unchecked proof is far more than a convention (S1).
- **Behind a safe API, in a module or crate of its own.** Domain code calls the wrapper and never
  sees `unsafe` (S2). "Safe" means no argument a caller can pass causes undefined behavior. A condition
  only the caller can guarantee keeps the function an `unsafe fn` whose `# Safety` section states
  it (S3, L9).
- **One unsafe operation per block**, so each `SAFETY:` comment justifies exactly one thing. A
  block doing three things under one comment invites the comment to cover only the first (L7).
  Inside an `unsafe fn` too, each unsafe operation sits in its own `unsafe` block, so the
  function's contract and each operation's proof stay apart (L8).

```rust
/// # Safety
/// `ptr` must point to `len` initialized bytes that stay valid and unchanged for `'buf`.
pub unsafe fn bytes<'buf>(ptr: *const u8, len: usize) -> &'buf [u8] {
    // SAFETY: the caller guarantees `len` initialized bytes at `ptr`, valid for `'buf`.
    unsafe { std::slice::from_raw_parts(ptr, len) }
}
```

The caller-held condition (`ptr` and `len`) can't be checked inside, so `bytes` stays `unsafe fn`;
a wrapper that owns the buffer, and so knows both, can offer a safe `as_bytes(&self) -> &[u8]`
instead.

## 2. Parse, don't validate

A *validation* checks a value and throws away what it found out. A *parse* checks the value and
returns a new type that remembers the result. After parsing, the type itself is the proof, so
nothing downstream has to check again, and nothing can forget to.

```rust
// Validation: callers must remember to ask, and the answer is thrown away.
fn is_valid_email(raw: &str) -> bool { /* … */ }
fn send_invite(to: &str) { /* was `to` checked? The signature can't say. */ }

// Parsing: the check returns the proof, and the signature demands it.
impl Email {
    pub fn try_new(raw: &str) -> Result<Self, InvalidEmail> { /* … */ }
}
impl FromStr for Email { /* calls Email::try_new: the text entry callers reach with .parse() */ }
fn send_invite(to: &Email) { /* `to` is a valid email; no check needed. */ }
```

**Rules, all checked in review:**

- At each inbound boundary, parse external data from network messages, files and other I/O, database
  rows, environment variables, CLI arguments, terminal input, IPC, FFI and any deserialization into
  domain types before domain logic. Serde, clap and SQLx are examples of adapters; the boundary
  exists wherever external data enters. Functions take `Email`, never the `&str` it came from, and
  code never checks the invariant again. Reloading from storage or the wire is a new boundary and
  parses again (S5). Outbound serialization starts from valid domain values and must not reveal
  secrets (S13).
- An `is_valid_x(&str) -> bool` or a `validate(&self)` over public fields becomes a constructor that
  returns the type (S6).
- A request, row or DTO is built from domain types: each field whose value has a refinement or tag
  uses it, and deserializing runs that type's constructor. The rules stay in the constructors and
  the format only touches shape. A primitive field lets the unparsed value travel past the
  boundary, where it can be forgotten or checked twice. A separate DTO, still built from domain
  types, exists only when the wire's shape differs from the domain's (names, nesting, flattening),
  or as the mirror serde needs to reach a cross-field constructor
  (`#[serde(try_from = "Raw")]`). Its `TryFrom` calls the domain type's constructor, so a rule
  that spans fields lives in one place and holds however the value is built (S7).

## 3. Newtypes: tags and refinements

A newtype wraps a primitive so that the compiler can tell values apart. A value gets one when it
carries an invariant, or when it could be swapped with another value of the same primitive, and
not otherwise: a local count or a one-off label with neither gains only a name (proportionality,
above) (S8). A newtype comes in one of two kinds, and its field's visibility says which.

```rust
pub struct UserId(pub u64);   // a tag: any u64 is a valid id; it only stops mix-ups
pub struct Email(String);     // a refinement: only Email::try_new can make one
```

- A **tag** has no invariant. It exists so that `transfer(from: AccountId, to: AccountId)` can't be
  called with a `UserId`. Its field is `pub`, and `#[serde(transparent)]` is fine, since there is
  nothing to check. `From` is fine where the two types make the meaning obvious (`From<u64> for
  UserId`). Where the primitive carries a unit or scale the target doesn't name, as in
  `From<u64> for Timestamp` (seconds? milliseconds?), `.into()` hides a guess (section 4) (S9). That
  `From` is also why a function takes `AccountId` itself, never `impl Into<AccountId>`: the
  generic accepts any bare `u64`, and the mix-up the tag exists to stop compiles again.

  ```rust
  fn close(id: impl Into<AccountId>) { … }
  close(order.customer_id.0);   // compiles: a customer's raw u64 becomes an AccountId

  fn close(id: AccountId) { … }
  close(order.customer_id.0);   // error[E0308]: expected `AccountId`, found `u64`
  ```

  A caller converting on purpose still can, in plain sight: `close(AccountId::from(raw))`. The rule
  is about the parameter accepting the primitive silently, not about conversion (S10).
- A **refinement** is any type with an invariant, whether it wraps one value or holds several (a
  `Span` whose `start < end`). Its fields are private to its module, not `pub(crate)`, so the
  constructor is the only way to make one; same-crate code can't slip past it either (S11).

| Lint | Catches |
| --- | --- |
| `partial_pub_fields` | a struct with some `pub` and some private fields |
| `missing_debug_implementations` | a public type without `Debug` |
| `derive_partial_eq_without_eq` | `PartialEq` derived where `Eq` could be |

A struct with both `pub` and private fields is half open, and the `pub` half lets callers break the
invariant the private half guards (L10). `Debug` is how a value shows up in a failing `assert_eq!`, in a
log and in a debugger, so a public type without it is a dead end (L11). Secrets still implement
`Debug`, by hand and redacted, and they have no `Display` or `Serialize` that could leak them (S13).
The rustc `missing_debug_implementations` lint covers public types only; review checks private
domain types (S12).

### `Eq` and reflexivity

`Eq` promises *reflexivity*: `a == a` for every value. `PartialEq` doesn't, because floats have
`NaN != NaN`. Without `Eq`, a type can't be a `HashMap` key, and some generic code won't accept it.
The compiler can't check reflexivity, because `Eq` has no methods. But
`derive_partial_eq_without_eq` fires only when every field is already `Eq`, so the derive it asks
for is reflexive by construction (L12). The danger is a hand-written `impl Eq`:

```rust
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Weight(f64);
impl Eq for Weight {}   // wrong: Weight(f64::NAN) != Weight(f64::NAN), so the promise is false

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Weight { grams: u64 }   // right: integer grams are Eq for real
```

When domain identity requires equivalence-relation equality, an inability to implement `Eq` may
reveal a modeling problem. For example, money should use integer minor units or decimal arithmetic
rather than binary floating-point. However, values intentionally following IEEE 754 semantics
legitimately implement `PartialEq` without `Eq` (S19). The one honest hand-written `Eq` is on a refinement whose invariant rules
out `NaN`, such as a finite-float type: its constructor makes reflexivity true, so the promise
holds (S14). `Hash` and `Ord` follow the same test, wherever the fields allow and the contract holds.

### Derive, unless the derived behavior is wrong

| Lint | Catches |
| --- | --- |
| `derivable_impls` | a hand-written `Default` a derive would produce |
| `expl_impl_clone_on_copy` | a hand-written `Clone` on a `Copy` type |
| `derived_hash_with_manual_eq`, `derive_ord_xor_partial_ord` (clippy defaults) | `Hash` or `Ord` derived beside a hand-written `PartialEq` or `PartialOrd`, which can disagree |

A derive is correct by construction and changes with the fields. A hand-written impl that does
what the derive would is code to read, and it goes stale when a field is added and the impl isn't
updated (L13, L14). So a trait is hand-written only where the derived behavior is *wrong* for the
type, and then every trait that must agree with it is hand-written too: `a == b` must imply equal
hashes, and `Ord` must agree with `==` (S15, L15). Every type derives `Debug`, `Clone` and
`PartialEq`, so tests compare values and callers copy them, and `Copy`, `Eq`, `Hash` and `Ord`
wherever the fields allow and the contract holds: a `Copy` value passes without ceremony, and
`Eq`, `Hash` and `Ord` let it key a map or sort (S18). The cases that come up:

- **A secret's `Debug`** is redacted by hand: the derived one prints the secret.
  `impl fmt::Debug for ApiKey { fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { f.write_str("ApiKey(***)") } }`
- **`Default`** is derived when the fields' defaults are the type's default, hand-written when the
  default is something else, and absent when no valid default exists. A refinement such as `Port`
  has none: the derive would build `Port(0)`, and the invariant forbids it (S16).
- **`Ord`**: the derive compares fields in declaration order and variants in declaration order.
  Declare them in the domain's order rather than hand-write the comparison. An order only one
  caller needs (orders by total, today) is a `sort_by_key` at that call, not the type's `Ord` (S17).

  ```rust
  #[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord)]
  pub enum Severity { Low, Medium, High, Critical }   // declared in order: Low < Critical
  ```

- **A finite float** is the one hand-written `Eq`, and the one place this goes wrong quietly.
  `-0.0 == 0.0` is true, but the two have different bits and `total_cmp` orders them apart, so a
  `Hash` over `to_bits()` or an `Ord` over `total_cmp` disagrees with `==`. Normalizing in the
  constructor keeps a single zero:

  ```rust
  #[derive(Debug, Clone, Copy, PartialEq)]
  pub struct Km(f64);   // finite, never negative

  impl Km {
      pub fn try_new(km: f64) -> Result<Self, InvalidKm> {
          if !km.is_finite() || km < 0.0 {
              return Err(InvalidKm);
          }
          Ok(Self(if km == 0.0 { 0.0 } else { km }))   // -0.0 becomes 0.0: one zero, one hash
      }
  }

  impl Eq for Km {}   // the constructor rejects NaN, so a == a for every Km
  impl Hash for Km {
      fn hash<H: Hasher>(&self, state: &mut H) { self.0.to_bits().hash(state) }
  }
  impl PartialOrd for Km {
      fn partial_cmp(&self, other: &Self) -> Option<Ordering> { Some(self.cmp(other)) }
  }
  impl Ord for Km {
      fn cmp(&self, other: &Self) -> Ordering { self.0.total_cmp(&other.0) }
  }
  ```

  Every other way to make a `Km` goes through `try_new` too, and arithmetic is no exception: two
  finite values can sum to infinity. An `impl Add for Km` can't say so, because its `Output` is a
  `Km`, and `Output = Result<Km, InvalidKm>` is too unusual to read as addition. So an operation
  that can break the invariant is a named method returning `Result`, named `try_*` as std names
  its `Result`-returning methods (`checked_*` returns `Option`, which means absence here) (S20):

  ```rust
  impl Km {
      pub fn try_add(self, rhs: Self) -> Result<Self, InvalidKm> {
          Self::try_new(self.0 + rhs.0)
      }
  }
  ```

## 4. One validating constructor, reached through std's traits

```rust
pub struct Port(NonZeroU16);

/// The constructor's only failure, so a unit struct.
#[derive(Debug, Clone, Copy, PartialEq, Eq, thiserror::Error)]
#[error("port must be non-zero")]
pub struct ZeroPort;

/// Text adds a syntax failure in front of the constructor's own.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ParsePortError {
    #[error("invalid port number: {0}")]
    Syntax(#[from] ParseIntError),
    #[error(transparent)]
    Zero(#[from] ZeroPort),
}

impl Port {
    pub const fn try_new(n: u16) -> Result<Self, ZeroPort> { /* … */ }
}
impl TryFrom<u16> for Port { /* calls Port::try_new */ }
impl FromStr for Port { /* parses the u16, then calls Port::try_new */ }
```

- **Every way in runs one validation.** `FromStr`, `TryFrom`, serde and the database decoder all
  run the same check, usually by calling the constructor; an owned `TryFrom<String>` may share
  the check and keep its allocation instead. With two checks, the rule ends up updated in one and
  forgotten in the other.
- **It's named `try_new`, following Google's Rust guide:** "If the constructor returns a `Result`,
  use `try_new()`." There are two reasons. In most languages `new` builds a value and that's all,
  so a reader coming to the code expects it to succeed. And it reads better: `Email::try_new(raw)?`
  says at the call site that this can fail, before anyone looks at the signature.
  The other constructor names come from the
  [Rust API Guidelines, C-CTOR](https://rust-lang.github.io/api-guidelines/predictability.html#c-ctor).
  A type that represents an I/O resource names its constructor in the domain's terms:
  `File::open`, `Mmap::open`, `TcpStream::connect`, `UdpSocket::bind`. A secondary constructor is
  prefixed `with_` (`Vec::with_capacity`), and a `from_` name marks a parse that chooses among
  forms (`Config::from_json`). These may return `Result` under their own names. A conversion is
  the trait itself: a `from_*` may sit beside it, never stand in for it (below). This guide departs
  from the API Guidelines and std in one place, for the two reasons above: they allow a `new` that
  returns `Result` (`NonZero::new`, `CString::new`), and here `new` always means "cannot fail".
- **It returns `Result`, never `Option`.** `Option` means "there is nothing here". A rejected input
  is a failure, and the caller should be told which one (see section 6).
- **Its error holds only the failures it can produce.** `Port::try_new` can fail one way, so its error
  is a unit struct. A shared `ValidationError { Empty, TooLong, BadChar, Zero }` would make every
  caller handle three cases that can't happen, and nobody could tell from the type which ones are
  real. `FromStr` wraps the constructor's error beside its own syntax failure, as `ParsePortError`
  does.
- **`Display` prints what `FromStr` parses back.** A value printed and parsed back gives the same
  value. The reverse need not hold when `FromStr` accepts several spellings: `"HIGH"` parses, and
  prints back as `high`. clap's `default_value_t` relies on the round trip, and a property test
  pins it (section 14).

| Lint | Catches |
| --- | --- |
| `infallible_try_from` | a `TryFrom` whose error is `Infallible` |
| `unnecessary_wraps` | a fn returning `Result` or `Option` that always returns `Ok` or `Some` |

A conversion that can't fail but is written as `TryFrom` makes every caller handle an error that
never happens. `From` is the honest signature. The same goes for a function that never fails but
returns `Result`: the caller writes dead error handling, and readers look for a failure case that
doesn't exist.

### Normalize in the constructor

The constructor brings the value to its canonical form first, by trimming and fixing case, so
that the derived `Eq`, `Hash` and `Ord` compare what the domain means. It must not erase a
difference the domain keeps.

```rust
impl Email {
    pub fn try_new(raw: &str) -> Result<Self, InvalidEmail> {
        let (local, domain) = raw.trim().split_once('@').ok_or(InvalidEmail)?;
        if local.is_empty() || domain.is_empty() {
            return Err(InvalidEmail);
        }
        // Domains are case-insensitive; the part before the @ may not be, so it's kept as typed.
        Ok(Self(format!("{local}@{}", domain.to_lowercase())))
    }
}
// FromStr and TryFrom<String> call this; Ann@Example.com == Ann@example.com,
// but Ann@example.com != ann@example.com
```

Normalize anywhere else and two equal values can compare unequal, so a `HashSet<Email>` holds the
same address twice. The same reasoning limits `Borrow<str>`: a `HashMap<Email, _>` looked up with a
`&str` hashes and compares the `str`, so `Borrow` is honest only when `Eq`, `Hash` and `Ord` on the
type agree with those on its text. After a normalization such as the email's, they don't, and a
lookup by the raw string misses an entry that is there.

### No back doors

The real promise is stronger than "there is a validating constructor": no value of the type can
exist that breaks its invariant, however it was obtained. One unchecked path undoes every check on
the others, so each path is closed or routed through the constructor.

- **Every other way to obtain a value keeps the invariant**: operators, mutating methods, and APIs
  behind a feature flag or `#[cfg(test)]` that a build can switch on. An operation that can break it
  (a sum past a bound) is a `try_*` method returning `Result`, never an operator (S20).

- **No `Deref` to the inner type.** It turns every `String` method into an `Email` method. Offer
  `as_str()`, `get()`, `AsRef` or `into_inner()` instead.
- **No `&mut` to the inner value.** A mutating method either keeps the invariant or doesn't exist.
- **No `Default`** unless the default value is valid.
- **serde goes through the constructor.**

  ```rust
  #[derive(serde::Deserialize, serde::Serialize)]
  #[serde(try_from = "String", into = "String")]   // right: a bad value fails deserialization
  pub struct Email(String);

  #[derive(serde::Deserialize)]
  #[serde(transparent)]                             // wrong: accepts "not-an-email"
  pub struct Email(String);
  ```

  A derived `Deserialize`, `#[serde(transparent)]` and `#[sqlx(transparent)]` all build the value
  without calling the constructor. A database `Decode` or `FromSql` decodes the inner type and
  calls `try_from`. A clap field of the type parses through `FromStr`; a closed set uses
  `ValueEnum`, which lists the choices in `--help`. A custom `value_parser` is a second way in,
  so it needs a stated reason.
- **A compile-time literal still calls `try_new`.** `const fn literal(n) -> Self` panics on failure,
  under an `#[expect(clippy::panic, reason = "…")]`, and is called only in `const` items. There, the
  panic happens at compile time, so an invalid literal fails the build:
  `pub const HTTP: Port = Port::literal(80);`. It is `pub(crate)`. Nothing stops another crate
  from calling a `pub` one at run time with a value from its users, and then it panics there. When
  another crate really needs the constants, make it `pub` with a `# Panics` doc section.

### Making a value from another, for every type

What the source is decides how the code is written. This holds for records, enums and tags as much
as for refinements.

- **A conversion turns a typed value into the same value in another type**, so it is a std trait:
  `From` when it can't fail, `TryFrom` when it fails instead of losing anything. Wrapping a
  primitive without a check, as a tag does, is a conversion too. Generic code, `.into()` and
  `.try_into()` find the trait; nobody finds an inherent `from_u16`. Such a method may stay beside
  the trait, but can't stand in for it. A name kept instead must say in its doc comment what the
  trait would hide: a loss, a rounding, an ambiguity or a choice. Merely describing the input is
  no reason. A constructor taking several values is not a conversion at all.
- **A trait impl promises an obvious conversion.** Std's `From` docs describe a strong convention,
  not a language rule: the conversion is lossless, value-preserving and obvious (std itself bends
  it where the difference is representational, as with `f32` to `f64`). This guide adopts the
  convention as policy, and `TryFrom` makes the same promise except that it fails instead of
  losing anything. Generic code calls `.into()` without reading a name, so an impl that rounds,
  truncates or picks one meaning among several surprises every caller. Such a conversion is a
  named function, whatever else the rules say: obviousness outranks trait conformity.
- **A unit the primitive doesn't carry is named, and typed once it travels.** A `u32` can't say
  "grams", so `From<u32> for Weight` would hide the unit and is ambiguous. Where the raw number
  enters, a named constructor says it, as `Weight::from_grams(u32)` and `Duration::from_secs`
  do; that is explicit, and a unit type there would be ceremony. Once bare quantities travel
  through the domain, though, grams and kilograms sit side by side in one primitive, and nothing
  stops one being passed for the other. Then the newtype rule of section 3 applies: give the unit
  a type, the conversion becomes obvious again (`impl From<Grams> for Weight`), and the mix-up no
  longer compiles. A change of unit is a conversion only when nothing is lost: grams to whole
  ounces rounds, so it is a named method (`Grams::to_whole_ounces`), never `From<Grams> for
  Ounces`, whose `.into()` would round silently in every caller.
- **A parse interprets a representation.** Text or bytes are read by a grammar or an encoding
  into a typed value. That is what separates it from a conversion: `Percentage::try_from(150u8)`
  checks a value but interprets nothing, so it is a conversion.
- **Complete text with one interpretation parses through `FromStr`**, which `.parse()`, clap and
  generic code reach for. A `parse_priority(&str)` or a `TryFrom<&str>` on its own leaves the type
  unreachable from all of them. What matters is one unambiguous interpretation, not one accepted
  spelling: `"HIGH"`, `"high"` and `"High"` may all parse, while `Display` prints one canonical
  form, so printing and parsing back still round-trip. A closed set's `ValueEnum` or serde names
  are its canonical text, and a `FromStr` for it accepts the same names.
- **Text `TryFrom` sits beside `FromStr`, with the same semantics.** It doesn't have to go through
  `FromStr`: `FromStr` receives `&str` and must allocate for an owned value, while a
  `TryFrom<String>` can run the same check and keep the caller's allocation. The rule is one
  validation and identical results, not one call path. `FromStr` returns an owned value, so a type
  that borrows from its input uses `TryFrom<&'a str>` or a named parser.
- **Bytes have no `FromStr`, and often no obvious trait either.** A complete, self-contained byte
  representation with one context-free interpretation may use `TryFrom<&[u8]>`. Most binary
  formats need more: a byte order, a protocol version, a decoding policy, a borrowed result or a
  stream. Those are named decoders, because the trait would hide the choice.
- **A parse that does more than read one value is a named function.** When it cuts the value out of
  a larger input (a URL's query string, a header before a body) or yields many values, a `parse_*`
  name says what it takes out. When the whole input is one collection, a collection type with its
  own `FromStr` is the better home, since the list then has a name and a trait. When it must choose
  something the input can't say (one format among several, a lossy or strict policy, extra context),
  a `from_*` name says the choice, as in `Config::from_json` or `String::from_utf8_lossy`. No trait
  can carry that information, so here the name is the right interface, not a way around one.

## 5. Types say what values mean

| Lint | Catches |
| --- | --- |
| `option_option` | `Option<Option<T>>` |
| `struct_excessive_bools` | a struct with more than three `bool`s |
| `fn_params_excessive_bools` | a fn with more than three `bool` parameters |

**Illegal states are unrepresentable.** If a value can hold a combination that means nothing,
some code somewhere will produce it.

```rust
// Eight combinations, three meaningful: tracking can exist on an unshipped order.
struct Order { is_paid: bool, is_shipped: bool, tracking: Option<TrackingNumber> }

// Only the real states exist, and tracking exists only once the order has shipped.
enum OrderState { Placed, Paid, Shipped { tracking: TrackingNumber } }
```

- Several `bool`s usually encode states that exclude each other. At a call site,
  `f(true, false, true, true)` can't be read without the definition open. The limit of three leaves
  room for flags that really are independent.
- A number that can't be zero is `NonZero*`. A field that exists only with another is one
  variant's data.
- `Option<Option<T>>` has three states (`None`, `Some(None)`, `Some(Some(x))`) and nothing names
  them. A reader has to guess which `None` means "not set" and which means "cleared". Use an enum
  whose variants say it.
- Absence is an `Option` or a variant. A sentinel such as `""`, `0` or `-1` must not stand for it,
  because the type can't tell a real `-1` from "none".
- A closed set of values, such as `small | medium | large`, is an enum (`#[derive(ValueEnum)]` for
  clap, `#[serde(rename_all = "…")]` for serde), not a refinement over a string. The compiler then
  knows every value, `match` stays exhaustive, and clap lists the choices in `--help`.
- State read from storage or the wire is an enum, not typestate. Typestate (`Order<Paid>`) checks
  transitions at compile time, but a row loaded at run time can be in any state.

**Variant fields are always public**, so an enum can't guard an invariant across its own fields.
Fields that share one go into a struct with private fields, which the variant wraps:

```rust
pub enum Window { All, Between { start: Timestamp, end: Timestamp } }  // end < start compiles

pub struct Span { start: Timestamp, end: Timestamp }  // Span::try_new rejects end <= start
pub enum Window { All, Between(Span) }
```

**Data with more than one field has named fields.** In `(u32, u32)` or `struct Size(u32, u32)`,
which one is the width? Name them: `struct Size { width: u32, height: u32 }`. A newtype's single
field is the exception.

## 6. `Option` is absence, `Result` is failure

The two types answer different questions. `Option` says whether there is a value. `Result` says
whether the operation worked. Using one for the other loses information.

```rust
// Wrong: a dead database reads as "no such order", and the caller creates a duplicate.
fn find(&self, id: OrderId) -> Option<Order> {
    self.store.load(id).ok().flatten()
}

// Right: found, not found and failed are three different outcomes, with three shapes.
fn find(&self, id: OrderId) -> Result<Option<Order>, StoreError> {
    self.store.load(id)
}
```

- A lookup that can fail returns `Result<Option<T>, E>`. `Ok(None)` is "not found", and `Err` is
  "the store failed".
- An operation that needs the value, like `ship(order_id)`, makes its absence an error variant
  (`OrderNotFound`), since for that operation, absence is a failure.
- A function that can't fail and may have nothing to return, such as `next_page()`, returns a
  plain `Option`.

| Lint | Catches |
| --- | --- |
| `unused_result_ok` | `r.ok();` used only to silence an unused `Result` |
| `let_underscore_must_use` | `let _ = r;` on a `#[must_use]` value |
| `ref_option` | a `&Option<T>` parameter (see section 10) |

`r.ok();` and `let _ = r;` both drop an error silently. `let _` is also clippy's own suggested fix
for `unused_result_ok`, which is why it's banned too. Sometimes dropping is right, such as a send
whose receiver may already be gone. Then say so with an `#[expect]`. An `.ok()` used as a value, as
in `find` above, slips past both lints, so review catches that one. `let _ignored = r` and `drop(r)`
also evade these lints; review checks whether the error is deliberately discarded.

## 7. Errors carry their cause

An error exists so that someone can act on it. That person might be a caller choosing what to do,
a test checking the right thing failed, or whoever reads the log at 3 a.m.

```rust
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum OrderError {
    #[error("cannot transition from {from} to {to}")]
    InvalidTransition { from: OrderStatus, to: OrderStatus },
    #[error("order store unavailable")]
    StoreUnavailable(#[source] StoreError),
}
```

| Lint | Catches |
| --- | --- |
| `result_unit_err` | a public fn returning `Result<_, ()>` |
| `map_err_ignore` | `.map_err(\|_\| …)`, which throws the cause away |
| `disallowed-types`: `anyhow::Error`, `anyhow::Result`, `eyre::Report`, `eyre::Result` | dynamic errors in library code |

- **Errors are typed.** `Err(())` says *that* something failed but not *what*, and it doesn't
  implement `std::error::Error`, so it composes with nothing. A `String` error can only be printed,
  not matched on. `Box<dyn Error>` also erases which failures a library function can return;
  use a typed error with variants for its possible failures. It implements
  `Error + Send + Sync + 'static` so it can cross threads and tasks, be returned from a spawned
  task, and be wrapped as a `#[source]` or boxed into `anyhow` at the edge without a wrapper.
- `result_unit_err` checks public functions only. Private helpers returning `Result<_, ()>` still
  lose the failure's meaning and require review.
- **The cause is kept.** `map_err(|_| …)` replaces the real cause (an `io::Error`, a parse error)
  with your own error and throws the original away. Wrap it with `#[source]` or `#[from]` so the
  chain survives. A domain or library API never exposes a dependency's error type directly,
  because then every caller depends on that library too. An infrastructure adapter whose natural
  contract is std's own error, such as a file store returning `io::Result`, is the exception: the
  type is already the shared vocabulary, as std itself shows. The lint misses a named cause
  converted to text, such as `map_err(|e| e.to_string())`; review checks that the source remains
  typed.
- **`anyhow` and `eyre` stay where errors only get printed:** `main`, a CLI command, a test. In a
  library, they hide the error's type, so callers can print it but can't match on it. The `Result`
  aliases are listed separately because banning `anyhow::Error` doesn't catch `anyhow::Result<T>`. A
  binary crate's own `clippy.toml` leaves these four entries out. Where `anyhow` is used, add
  `.context(...)` so the printed chain says what was being attempted.
- **Errors derive `Clone, PartialEq, Eq`** so tests can `assert_eq!` on them, unless a cause can't
  (`io::Error` has none of them). An error whose fields are all `Copy` derives `Copy` too, so it
  passes by value like the unit-struct `ZeroPort`.
- **Messages are lowercase with no trailing period**, because they get chained into
  `outer: inner: cause`. They say what is wrong and never echo secret input. An
  `InvalidToken(String)` holding the rejected token puts the secret into every log line and panic
  message that prints the error.

## 8. Failure is a value, not a crash

| Lint | Catches |
| --- | --- |
| `unwrap_used`, `expect_used` | `.unwrap()`, `.expect()` outside tests |
| `panic` | `panic!` outside tests |
| `todo`, `unimplemented` | placeholders that panic when reached |
| `unreachable` | `unreachable!()` |
| `disallowed-methods`: `catch_unwind`, `process::abort` | catching a panic or aborting the process |
| `disallowed-methods`: `PoisonError::into_inner`, `get_ref`, `get_mut` | reading a lock a panic left poisoned |
| `cast_possible_truncation`, `cast_sign_loss`, `cast_possible_wrap` | an `as` cast that truncates, drops the sign or wraps |
| `string_slice` | `&s[a..b]` on a `str` |
| `exit`, `dbg_macro`, `print_stdout`, `print_stderr` | process exit, debug and print macros |
| clippy.toml: `allow-unwrap-in-tests`, `allow-expect-in-tests`, `allow-panic-in-tests`, `allow-dbg-in-tests`, `allow-print-in-tests` | lets tests do all of the above |

A panic takes failure out of the type system. The caller can't see it in the signature, can't match
on it and can't recover from it. In a server, it kills the request's task or, under
`panic = "abort"`, the whole process. That is why functions are *total*: every valid input gives a
value, and every failure is an `Err` the caller has to handle. User input is never checked with
`assert!`, because bad input is expected, not a bug.

- `unwrap` and `expect` are panics with a shorter name. `expect` gets one exception: bootstrap in
  `main.rs`, where crashing with a clear message *is* the right thing to do. It sits under an
  `#[expect]` that says so. Bootstrap means the environment failing at startup, such as a missing
  config file or a port that won't bind. A user mistyping an argument is not bootstrap. A panic
  prints `thread 'main' panicked at src/main.rs` and exits with code 101, where a user expects a
  usage message and an error code, so CLI input is parsed and its error reported.
- `todo!` and `unimplemented!` are panics that ship by accident.
- `unreachable!` claims something the compiler doesn't check. An exhaustive `match`, or a type that
  can't hold the impossible case, makes the compiler check it.
- **A bug is not an error, and not a default either.** Banning panics must not push code into
  pretending. `Result` is for failures a caller can act on: bad input, an unavailable store. A
  broken precondition or an impossible state is a bug. Dressing it up as an error variant gives
  callers a case they can't handle, and papering over it with a fallback (`unwrap_or_default()`)
  hides it until the data is wrong. Fix the API or the types so the state can't arise. When even
  an exhaustive match or a type can't express it, the narrow exception is a reasoned
  `#[expect(clippy::unreachable, reason = "…")]` at that spot, where every reader sees the claim.
- **A poisoned lock stays shut.** A lock is poisoned when a thread panicked while holding it, which
  means an update may have stopped halfway and the data may break its own invariants.
  `PoisonError::into_inner` reads it anyway, so the half-done update becomes the state everyone
  works from. The poisoning is reported as an error instead, like any other failure the caller
  can't fix in place.

  ```rust
  // wrong: carries on from whatever the panicking thread left half-done
  let mut cache = self.cache.lock().unwrap_or_else(PoisonError::into_inner);

  // right: the poisoning is a failure the caller sees
  #[expect(clippy::map_err_ignore, reason = "PoisonError holds the guard, so it can't be a #[source]")]
  let mut cache = self.cache.lock().map_err(|_| CacheError::Poisoned)?;
  ```

  The one recovery that never reads the old data is rebuilding it: take the guard, overwrite the
  whole value, then `clear_poison`, under a reasoned `#[expect(clippy::disallowed_methods)]`. A lock
  that doesn't poison (`tokio::sync::Mutex`, `parking_lot`) leaves the same half-done data after a
  panic with no flag at all, so no lint helps there: keep the code holding it panic-free.
- `catch_unwind` is banned because recovering from panics is not error handling. It also does
  nothing when the binary is built with `panic = "abort"`.
- `process::abort` also stops the process without running destructors. `process::exit` is caught by
  its own lint outside `main`. Neither belongs in a library.
- The `panic` lint does not catch `assert!` on external input. Review checks assertions against
  values that can arrive from users or I/O.
- **An `as` cast between integers never fails, so it gets the value wrong instead.** `300u64 as u8`
  is `44`, `-1i64 as u64` is `18446744073709551615`, and `u64::MAX as i64` is `-1`. The three cast
  lints catch those casts. Use `From` when the conversion can't lose anything, and `TryFrom` when
  it can, so the error reaches the caller.
- **Slicing a `str` at a byte offset panics** when the offset lands inside a multi-byte character:
  `&"aé123"[..2]` panics, because `é` takes two bytes. `string_slice` catches `&s[a..b]`. Nothing
  catches `split_at`, so review does. Use `split_once`, `char_indices` or `s.get(a..b)`, which
  returns `None` instead of panicking.
- **Indexing a slice or `Vec` at input-dependent bounds can panic.** Use `get` or `get_mut` and
  handle the missing element or range. `indexing_slicing` is too noisy for this lint set, so review
  checks it.
- **Arithmetic that can overflow panics in a debug build and wraps in release.** For money and
  quantities, both are wrong: `cents * percent` can overflow on a large order. Use `checked_mul` and
  friends and return an error. Clippy's lint for this, `arithmetic_side_effects`, flags every `+`
  and `*`, which is too noisy to enable, so review catches it.
- **Division and remainder by zero panic in all builds.** When a divisor can be zero, check it or
  use `checked_div`/`checked_rem` and return an error. Money uses integer minor units or a decimal
  type; binary floats can round amounts and are not suitable for exact accounting.
- **Library code returns failures to its caller.** `process::exit` skips destructors and stops the
  process. `dbg!` and print macros leak debugging or write output the caller did not request;
  use structured logging when observation is needed. Binary entry points may print deliberately.

In a test, a panic is how the test fails, so unwrapping there is the assertion. The
`allow-*-in-tests` settings let `#[test]` functions and `#[cfg(test)]` code do that. A helper file
under `tests/` is neither, so it returns `Result` and uses `?`.

## 9. Matches keep up with enums

| Lint | Catches |
| --- | --- |
| `wildcard_enum_match_arm` | `_ =>` covering several variants of an enum |
| `match_wildcard_for_single_variants` | `_ =>` covering exactly one variant |

An exhaustive `match` is a checklist the compiler keeps for you. When someone adds a variant, every
`match` that lists variants by name stops compiling until it decides what the new variant means. A
`_ =>` arm silently handles the new variant the same way as whatever it was covering before, and
that is usually wrong.

```rust
match status {
    Status::Paid => ship(order),
    _ => {}   // a new Status::Refunded lands here, silently, and nobody decided that
}
```

**`#[non_exhaustive]` stays off your own enums.** Inside the defining crate the attribute does
nothing. In every *other* crate, including the other crates in your workspace, it forces a `_` arm,
which throws this check away. Its purpose is a crate published to users you don't rebuild, where
adding a variant would otherwise be a breaking release. In a workspace built together, you *want*
a new variant to break the build.

On another crate's `#[non_exhaustive]` enum, a `_` arm is required. List every variant you know
before it, and the lint asks for exactly that. If only one or two matter, use `matches!` or
`if let`.

## 10. Ownership is borrowed unless it's needed

| Lint | Catches |
| --- | --- |
| `needless_pass_by_value` | a parameter taken by value but never consumed |
| `ref_option` | a `&Option<T>` parameter |
| `redundant_clone` | a clone whose original is never used again |

This is the second idea in practice. A signature that takes ownership forces callers to give theirs
up or to clone. Asking for more than the function uses costs every caller. So take `&T`, `&str` or
`&[T]` when you only read, and `Option<&T>` rather than `&Option<T>`, which any caller can produce,
even one that holds a `T` and no `Option`. Take ownership when storing, returning or consuming the
value. Clippy already flags `&String`, `&Vec` and `&Box` parameters by default. A clone whose
original is never used again is pure cost: move the value instead. If a clone only quiets a borrow
error, shorten the borrow or change the API to make the needed ownership clear.

**Shared ownership is for shared lifetimes.** `Rc` and `Arc` keep a value alive until the last
clone is dropped, wherever that is, so ownership stops being visible: nobody can say when the value
goes, a cycle of them never goes at all (break it with `Weak`), and each clone and drop of an
`Arc` updates an atomic counter. That is the right price where the lifetime really is shared:
`tokio::spawn` needs `'static` futures, so state that spawned tasks or request handlers hold is an
`Arc`, and frameworks such as axum ask for `Clone + 'static` state. It is the wrong price for
escaping a borrow error, which is the clone-to-quiet-the-borrow-checker case above in another
form. Many handles are already an `Arc` inside (sqlx's `Pool`, reqwest's `Client`); clone those
directly instead of wrapping them in a second `Arc`.

**Domain values don't mutate behind your back.**

| Entry in `disallowed-types` | Reason |
| --- | --- |
| `std::cell::Cell`, `std::cell::RefCell` | "domain types hold no interior mutability" |
| `std::sync::Mutex`, `std::sync::RwLock` | the same |

Interior mutability lets code change a value through a shared `&` reference, so a reader can't
trust that a value they hold a shared reference to is still what it was. A domain type that
changes only through `&mut self` makes every change visible in signatures, and the borrow checker
rules out races. When a value must be shared across tasks, the *caller* wraps it, as
`Arc<Mutex<Order>>`. The domain type stays plain. These bans apply to domain crates only:
infrastructure code, such as connection pools and caches, legitimately needs locks. Atomics and
`OnceCell` have no lint, so review catches them in domain code.

## 11. Hidden inputs are passed in

| Entry in `disallowed-methods` | Reason |
| --- | --- |
| `SystemTime::now`, `Instant::now`, `chrono::Utc::now` | "pass the time in" |
| `rand::random`, `rand::rng`, `rand::thread_rng` | "pass the source of randomness in" |
| `uuid::Uuid::new_v4`, `uuid::Uuid::now_v7` | "pass the id in" |
| `disallowed-macros`: `ctor::ctor`, `dtor::dtor` | code that runs before or after `main` |

`iter_over_hash_type` flags `for` loops over a `HashMap` or `HashSet`, but not iterator chains such
as `map.keys().collect()`. Review checks those chains and whether order can affect domain output or
decisions. When it does, use an ordered collection or sort before using the items. When a flagged
loop's order cannot matter, explain the exception with `#[expect]`.

If a function reads the clock or a random generator inside, its signature lies. It looks like the
same inputs always give the same output, but they don't.

```rust
// Untestable: "the day the trial expires" can't be reached without waiting for it.
fn is_expired(&self) -> bool { Utc::now() > self.expires_at }

// Time is just a value: a test picks the moment it needs.
fn is_expired(&self, now: DateTime<Utc>) -> bool { now > self.expires_at }
```

**No code runs before or after `main`.** A `#[ctor]` function runs when the binary loads, in an
order no file shows, before logging or configuration exist, and a failure there has no caller to
return to. A `#[dtor]` runs after `main`, when other parts may already be gone. Both are hidden
inputs of the whole program. Startup belongs in `main`, which calls each step in order and handles
its errors, and builds what the rest needs to pass it in; teardown belongs to `main` or to the
`Drop` of the value that owns the resource.

The production caller reads the clock once, in the binary that wires everything together. `rand`
0.9 renamed `thread_rng` to `rng`, so both are listed. `uuid`'s v4 and `now_v7` read randomness and
the clock, while `Uuid::new_v7(ts)` takes its time as a parameter, so it stays allowed. These bans
apply to domain crates.

## 12. Async code doesn't block, deadlock or lose `Send`

| Lint | Catches |
| --- | --- |
| `await_holding_lock` | a std `MutexGuard` held across `.await` |
| `await_holding_refcell_ref` | a `RefCell` borrow held across `.await` |
| `future_not_send` | an `async fn` whose future is not `Send` |
| `let_underscore_future` | `let _ = future` discarding an unpolled future |

Each `.await` is a point where the task can pause while other tasks run.

- A std `Mutex` locked across that pause stays locked while the task sleeps. Any other task that
  wants the lock blocks a runtime thread, and if that task runs on the same thread, nothing ever
  makes progress. Release the guard before the `.await`, or use an async-aware lock.
- A `RefCell` borrowed across the pause can panic at run time when another task borrows it.
- A multithreaded runtime moves tasks between threads, so `tokio::spawn` needs a `Send` future. If
  the future isn't `Send`, the compile error shows up at the `spawn`, often far from the
  `Rc` or guard that caused it, with a long message. This lint reports it at the function that
  creates the future, where the fix is. A trait whose futures get spawned declares
  `-> impl Future<Output = …> + Send` for the same reason.
- `future_not_send` also flags a future intended only for a local executor. Such a future is valid;
  document that exception with a reasoned `#[expect]`.
- An async operation is lazy: `let _ = send()` drops its future without running it. Await, return
  or deliberately spawn it. A spawned task's `JoinHandle` must be awaited or supervised so its
  error and panic are observed; detached work needs an owner and a failure path. The lint misses
  `let _future = send()`, which also leaves it unpolled, so review catches it.

**Review checks blocking, cancellation and spawned task ownership:**

- **Blocking calls stay off the runtime.** `std::fs`, a synchronous HTTP client or heavy CPU work
  inside an `async fn` stalls every task on that thread. Use the async API or `spawn_blocking`.
- **Every `.await` is a cancellation point.** A timeout, a `select!` or a client disconnecting can
  drop the future there, and the code after that `.await` never runs:

  ```rust
  async fn capture(&self, payment: &Payment) -> Result<(), CaptureError> {
      self.gateway.charge(payment).await?;   // money has moved
      self.ledger.record(payment).await?;    // dropped here: charged, never recorded
      Ok(())
  }
  ```

  Not every partial effect is a bug: Tokio documents `write_all` as not cancellation-safe, and a
  partial write is often fine. The requirement is that cancellation never breaks a domain
  invariant or silently loses progress the application needs. Where an operation can stop
  halfway, the caller decides on purpose: preserve the progress, recover, compensate, or accept
  the partial outcome and say so. A charge without its record fails that test; how to fix it, by
  ordering the steps or making a retry harmless, is a design decision. The Rust fact is that the
  drop can happen at any `.await`.

## 13. Code says what it does, plainly

| Lint | Catches |
| --- | --- |
| `wildcard_imports` | `use foo::*` (except `use super::*` in tests, and preludes) |
| `needless_for_each` | `.for_each(…)` where a `for` loop reads plainer |

A glob import hides where a name comes from. It also lets a new item added upstream shadow, or
clash with, one of yours, with no change in your file. A `for` loop says "loop" in one word.
`.for_each(|x| …)` says the same thing in a combinator and makes `break`, `continue` and `?`
awkward.

**Review checks the rest:**

- **Names say what something is or does.** `Service`, `Manager`, `Helper`, `Utils` and `Misc` say
  only that something exists. `CaptureService` could do anything, while `ChargeCard` or
  `LoadOrders` names the job. An abbreviation only insiders know, or one made by dropping letters
  (`cnt`, `mgr`), costs every newcomer a lookup. A single letter is fine for a lifetime or generic
  parameter whose role is plain (`'a` tying an output to an input, `T` in a container); where
  several are in play, names say which is which (`'input`, `S: Store`).
- **Accessors follow std's names**, so callers guess them right: `foo()` returns a reference (or a
  `Copy` value), `foo_mut()` a mutable one, `set_foo()` replaces, `take_foo()` empties and returns
  the old value, `replace_foo()` sets and returns it. A `get_` prefix adds nothing. A refinement's
  `get()`, as on `NonZeroU16`, is the whole value, not a field.
- **A trait needs a real abstraction need.** A trait with one implementation and no other use adds
  a name and an indirection that every reader has to step through, and it hides which code
  actually runs, all for flexibility nobody uses yet. Write the concrete type first. A trait earns
  its place with a second implementation, a test double standing in for the network, disk or
  clock, implementors outside the crate, or a generic algorithm written against it. An extension
  trait earns it differently: the orphan rule forbids inherent methods on a type from another
  crate, so a trait is the only way to add them. Its `Ext` suffix (`ResponseExt`) tells the reader
  it exists for its methods, not for generics or `dyn`.

  ```rust
  pub trait DurationExt {
      fn whole_minutes(&self) -> u64;
  }

  impl DurationExt for std::time::Duration {
      fn whole_minutes(&self) -> u64 { self.as_secs() / 60 }
  }
  ```

  A trait implemented for several foreign types so that generic code can take any of them
  (`trait Timestamped` for `SystemTime` and `chrono::DateTime`) is not an extension trait: it is
  the generic-algorithm reason, and it gets no `Ext`. A method on your own type is never an
  extension trait: write it inherent.
- **An operator does what its symbol says.** `+` adds, `*` multiplies, `!` negates. An `Add` that
  appends to a log or a `Shl` that sends a message reads as arithmetic, so the reader has to look
  it up to learn it isn't; a named method says what happens.
- **A macro is the last resort.** Macros hide control flow, give worse error messages and confuse
  tooling. Try a function, a type or a trait first, then `macro_rules!`, and a proc macro only
  after that.

## 14. Tests pin behavior, not the compiler

| Lint | Catches |
|---|---|
| `assertions_on_result_states` | `assert!(r.is_err())`, `assert!(r.is_ok())` |

`assert!(r.is_err())` checks only that *some* error happened, so the test still passes if the code
fails for the wrong reason. Assert the specific error, which errors can do because they derive
`PartialEq` (section 7):

```rust
assert!(Port::try_new(0).is_err());            // passes even if it fails for another reason
assert_eq!(Port::try_new(0), Err(ZeroPort));   // passes only for the right reason
```

Clippy suggests `r.unwrap_err()` instead, but that checks no more than the original, so don't take
the suggestion.

**Review checks the rest:**

- **One accepted input per constructor, and every rejection reason reached by a test that asserts
  that error.** A rejection no test reaches can be deleted and nothing goes red.
- **No second example of a rule already pinned, and no tests of derives, getters or anything else
  the compiler guarantees.** They cost upkeep and prove nothing.
- **Where a law exists, a property test replaces examples.** Where `Display` is the type's
  canonical text, the one `FromStr` reads, a property test pins that its printed form parses back.
  Rust doesn't promise `Display` is lossless or machine-readable, so a type whose `Display` is
  only for people needs no such test:

  ```rust
  proptest! {
      #[test]
      fn port_display_parses_back(n in 1u16..) {
          let port = Port::try_from(n).expect("generated port is nonzero");
          prop_assert_eq!(port.to_string().parse::<Port>(), Ok(port));
      }
  }
  ```

- **Every forbidden state transition the types can't rule out has a test.** Integration tests in
  `tests/` use only the public API, as real callers do.

## What came from Google's Rust style guide

In November 2026 the guide was checked against
[Google's Rust style guide](https://google.github.io/styleguide/rustguide.html). Much of Google's
guide is specific to Chromium, Android or Fuchsia (file layout, gtest, sequences instead of
threads, no async), and that part doesn't apply here.

**Adopted:**

| From Google | Here |
| --- | --- |
| No glob imports | `wildcard_imports` (section 13) |
| A `for` loop, not `for_each` | `needless_for_each` (section 13) |
| Borrow flexibly: `Option<&T>`, not `&Option<T>` | `ref_option` (section 10), plus `avoid-breaking-exported-api = false` so it reaches public functions too |
| Don't rely on catching panics | `catch_unwind` in `disallowed-methods` (section 8) |
| Named fields, not tuples | Named fields beyond a newtype (section 5) |
| Macros last | A function, type or trait before a macro (section 13) |
| `#[non_exhaustive]` only where breakage can't be fixed in place | Never on your own enums inside a workspace (section 9) |
| On someone else's non-exhaustive enum, list the known variants | Already what `wildcard_enum_match_arm` asks for (section 9) |
| A constructor that returns `Result` is `try_new` | The same rule (section 4). Until November 2026 this guide used `new` |
| `Eq` is a promise the compiler can't check | Reflexivity spelled out; `Eq` by derive, by hand only where the invariant guarantees it (section 3) |
| Extension traits, named `…Ext` | A fifth reason for a trait (section 13); until then this guide flagged them |
| Application code almost never takes `impl Into<T>` | Never for a newtype: it lets the primitive back in (section 3) |
| Operators only for their mathematical meaning | Section 13 |
| Accessor names (`foo`, `foo_mut`, `set_foo`, `take_foo`, `replace_foo`) | Section 13 |
| Avoid abbreviations; name lifetimes and generic parameters | Section 13 |
| Error types `Copy` where possible | `Copy` where the fields allow (section 7) |
| Never reach inside a poisoned mutex | `PoisonError` accessors in `disallowed-methods` (section 8) |
| Unsafe in a small safe abstraction, with a justification | Fenced in a module or crate of its own, one operation per block, a benchmark when the reason is speed (section 1) |
| `#[derive]` where possible | Derive unless the derived behavior is wrong; `derivable_impls`, `expl_impl_clone_on_copy` (section 3) |
| No code before `main` | `ctor`/`dtor` in `disallowed-macros` (section 11) |

The same review also adopted one point from a video walkthrough of Google's guide, the presenter's
own preference rather than Google's rule: `Option` means absence and `Result` means failure. A
constructor now returns `Result`, never `Option`, with an error holding only its own failures
(sections 4 and 6). Before that, this guide followed `NonZero::new` and allowed `Option` for one
self-evident failure.

**Already here, often more strictly:** an enum instead of a bool parameter, a newtype instead of a
type alias, pattern matching instead of check-then-unwrap, borrowing instead of cloning, a
`SAFETY:` comment on `unsafe`, a trait only for a real abstraction need, and `#[non_exhaustive]`
(on enums and structs alike) only in a crate published to users you don't rebuild.

**Held by clippy's default lints**, which `cargo clippy -- -D warnings` already denies:
`as_`/`to_`/`into_` receivers (`wrong_self_convention`), a std trait instead of a look-alike method
(`should_implement_trait`), `is_empty` beside `len` (`len_without_is_empty`), `Default` beside an
argument-free `new` (`new_without_default`), and `&T` over `&Box<T>`, `&[T]` over `&Vec<T>`
(`borrowed_box`, `ptr_arg`).

**Kept against Google, on purpose:**

- **`Eq` wherever it holds.** Google prefers `PartialEq` alone, because adding `Eq` to a published
  type is a promise that is hard to take back. Here, domain types need `Eq` to be map keys, and the
  derive can't be wrong (section 3). A crate published for others to depend on may drop the lint and
  add `Eq` only where it means to promise it.
- **No `panic!` for broken invariants.** Google allows it. This guide makes functions total
  (section 8), which Google itself notes some codebases do.
- **`Arc` where the lifetime is shared.** Google says to avoid `Rc` and `Arc` unless the
  alternative is unreasonably complex, which fits Chromium, where async is banned and work runs
  on sequences. An async backend can't follow it: a spawned task can't borrow from its spawner,
  so state the tasks share is an `Arc`. What carries over is the reason behind Google's rule:
  shared ownership hides when a value goes, so it is used only where the lifetime really is
  shared, never to escape a borrow (section 10).

**Not taken:** required `#[must_use]` (`Result` is already must-use, and the lint is noisy), required
doc comments (too noisy for application code), extra type annotations, and `format!` instead of
`+`. Also not taken, as library ergonomics or performance this guide ranks below simplicity:
generics over `dyn Trait` in parameters, returning iterators and taking `IntoIterator`. Import
and file-layout conventions (one module per `use`, free functions called through their module,
files named after their main item) are left to rustfmt and to the architecture guide; rustfmt's
`imports_granularity` is nightly-only. Smaller points left to review judgment: `#[doc(hidden)]`
items treated as private, `const fn` as a stability promise in a published crate, assertion
messages, iterator chains kept out of `for` headers, and `#[rustfmt::skip]` only for alignment.

## Settings that only make the files work

- **`allow-invalid = true`** on library paths (`anyhow`, `chrono`, `rand`, `uuid`) keeps an entry
  quiet in a crate that doesn't depend on that library. Without it, clippy warns that the path
  doesn't resolve, and the same file couldn't serve every crate.
- **Entries marked "domain crates only" or "library crates only"** are left out of the copy of
  `clippy.toml` in crates where they don't apply. A binary prints `anyhow` errors and reads the
  clock, and an infrastructure crate holds locks.

# Why the Rust style guide says what it says

This file is for people. It gives the reason behind every rule in [SKILL.md](../SKILL.md) and every
entry in [`assets/lints.toml`](../assets/lints.toml) and [`assets/clippy.toml`](../assets/clippy.toml),
with examples. If a lint fired on your code, search this page for its name. Sections are grouped by
the problem they prevent. Each one gives the reason, then the lints that enforce it, then what
review has to check by hand.

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

## How the lint configuration works

Five decisions shape the whole setup.

- **The machine checks what a machine can check.** You can't argue a lint out of a verdict, and it
  doesn't get tired. A reviewer, human or model, can be argued with and does get tired. So every
  rule that clippy or rustc can hold is handed to them, and review covers only the rest.
- **Every lint is `deny`, not `warn`.** Warnings pile up until nobody reads them. A lint that matters
  fails the build, and a lint that doesn't matter isn't on the list.
- **Exceptions are written down where they happen.** A lint is never turned off for a whole crate
  because one place needs an exception. That place gets `#[expect(clippy::name, reason = "…")]`,
  and the `reason` tells the next reader why. `expect`, unlike `allow`, fails once the lint stops
  firing, so a stale exception can't linger. `allow_attributes` bans a bare `#[allow]`, and
  `allow_attributes_without_reason` bans an exception with no `reason`.
- **Public signatures are linted like private ones** (`avoid-breaking-exported-api = false`).
  Clippy normally leaves public signatures alone so that it doesn't push a breaking release. In a
  workspace you rebuild, changing a public signature is a refactor, not a release. A crate published
  to outside users drops this line, and for the same reason it may use `#[non_exhaustive]` (see
  section 7).
- **Default lints are still listed.** Six entries (`infallible_try_from`, `result_unit_err`,
  `await_holding_lock`, `await_holding_refcell_ref`, `disallowed_types`, `disallowed_methods`) are
  already on in clippy by default. They are listed anyway, so that the file states every rule it
  holds and raises them to `deny`.

## 1. Memory safety stays the compiler's job

| Lint | Catches |
| --- | --- |
| `unsafe_code = "forbid"` | any `unsafe` |
| `undocumented_unsafe_blocks` | an `unsafe` block with no `// SAFETY:` comment |

Rust's main promise is that safe code can't corrupt memory. An `unsafe` block is a proof the
compiler can't check, and domain or backend code almost never needs one. `forbid` is stricter than
`deny`: no attribute in the code can lift it, so nobody quietly opts out. A crate that really needs
`unsafe`, such as an FFI wrapper, lowers this one lint to `deny` and puts an
`#[expect(unsafe_code, reason = "…")]` on each item. Then the `// SAFETY:` comment states the
invariant the block relies on, so a reviewer can check the proof the compiler couldn't.

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
fn send_invite(to: &Email) { /* `to` is a valid email; no check needed. */ }
```

**Rules, all checked in review:**

- Raw input becomes its type as soon as it's read. Functions take `Email`, never the `&str` it came
  from, and code never checks the invariant again.
- An `is_valid_x(&str) -> bool` or a `validate(&self)` over public fields becomes a constructor that
  returns the type.
- A record, row or DTO is deserialized as is, with plain fields, and then converted with
  `impl TryFrom<Dto> for Domain`. Deserializing straight into the domain type would mix the format
  with the rules.

## 3. Newtypes: tags and refinements

A newtype wraps a primitive so that the compiler can tell values apart. A value gets one when it
carries an invariant, or when it could be swapped with another value of the same primitive. A
newtype comes in one of two kinds, and its field's visibility says which.

```rust
pub struct UserId(pub u64);   // a tag: any u64 is a valid id; it only stops mix-ups
pub struct Email(String);     // a refinement: only Email::try_new can make one
```

- A **tag** has no invariant. It exists so that `transfer(from: AccountId, to: AccountId)` can't be
  called with a `UserId`. Its field is `pub`, and `From<u64>` and `#[serde(transparent)]` are fine,
  since there is nothing to check.
- A **refinement** has an invariant. Its fields are private, so the constructor is the only way to
  make one.

| Lint | Catches |
| --- | --- |
| `partial_pub_fields` | a struct with some `pub` and some private fields |
| `missing_debug_implementations` | a public type without `Debug` |
| `derive_partial_eq_without_eq` | `PartialEq` derived where `Eq` could be |

A struct with both `pub` and private fields is half open, and the `pub` half lets callers break the
invariant the private half guards. `Debug` is how a value shows up in a failing `assert_eq!`, in a
log and in a debugger, so a public type without it is a dead end. Secrets still implement `Debug`,
by hand and redacted, and they have no `Display` or `Serialize` that could leak them.

### `Eq` and reflexivity

`Eq` promises *reflexivity*: `a == a` for every value. `PartialEq` doesn't, because floats have
`NaN != NaN`. Without `Eq`, a type can't be a `HashMap` key, and some generic code won't accept it.
The compiler can't check reflexivity, because `Eq` has no methods. But
`derive_partial_eq_without_eq` fires only when every field is already `Eq`, so the derive it asks
for is reflexive by construction. The danger is a hand-written `impl Eq`:

```rust
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Weight(f64);
impl Eq for Weight {}   // wrong: Weight(f64::NAN) != Weight(f64::NAN), so the promise is false

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Weight { grams: u64 }   // right: integer grams are Eq for real
```

A domain value that can't be `Eq` usually points to a modeling bug. Money as `f64` should be integer
cents or a decimal type.

## 4. One constructor, named `try_new`, that says exactly how it fails

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

- **Every way in goes through one constructor.** `FromStr`, `TryFrom`, serde and the database
  decoder all call it. With two paths, the rule ends up checked in one and forgotten in the other.
- **It's named `try_new`, following Google's Rust guide:** "If the constructor returns a `Result`,
  use `try_new()`." There are two reasons. In most languages `new` builds a value and that's all,
  so a reader coming to the code expects it to succeed. And it reads better: `Email::try_new(raw)?`
  says at the call site that this can fail, before anyone looks at the signature.
  The other constructor names come from the
  [Rust API Guidelines, C-CTOR](https://rust-lang.github.io/api-guidelines/predictability.html#c-ctor).
  A type that represents an I/O resource names its constructor in the domain's terms:
  `File::open`, `Mmap::open`, `TcpStream::connect`, `UdpSocket::bind`. A conversion constructor is
  prefixed `from_` (`String::from_utf8`), and a secondary constructor is suffixed `with_`
  (`Vec::with_capacity`). These may return `Result` under their own names. This guide departs
  from the API Guidelines and std in one place, for the two reasons above: they allow a `new` that
  returns `Result` (`NonZero::new`, `CString::new`), and here `new` always means "cannot fail".
- **It returns `Result`, never `Option`.** `Option` means "there is nothing here". A rejected input
  is a failure, and the caller should be told which one (see section 6).
- **Its error holds only the failures it can produce.** `Port::try_new` can fail one way, so its error
  is a unit struct. A shared `ValidationError { Empty, TooLong, BadChar, Zero }` would make every
  caller handle three cases that can't happen, and nobody could tell from the type which ones are
  real. `FromStr` wraps the constructor's error beside its own syntax failure, as `ParsePortError`
  does.
- **`Display` is `FromStr`'s exact inverse.** A value printed and parsed back gives the same value.
  clap's `default_value_t` relies on this, and a property test pins it (section 12).

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
// Ann@Example.com == Ann@example.com, but Ann@example.com != ann@example.com
```

Normalize anywhere else and two equal values can compare unequal, so a `HashSet<Email>` holds the
same address twice.

### No back doors

A refinement must not hand out a way around its constructor.

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
  calls `try_from`. A clap field of the type parses through `FromStr`, with no custom
  `value_parser`.
- **A compile-time literal still calls `try_new`.** `const fn literal(n) -> Self` panics on failure,
  under an `#[expect(clippy::panic, reason = "…")]`, and is called only in `const` items. There, the
  panic happens at compile time, so an invalid literal fails the build:
  `pub const HTTP: Port = Port::literal(80);`. It is `pub(crate)`. Nothing stops another crate
  from calling a `pub` one at run time with a value from its users, and then it panics there. When
  another crate really needs the constants, make it `pub` with a `# Panics` doc section.

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
| `ref_option` | a `&Option<T>` parameter (see section 9) |

`r.ok();` and `let _ = r;` both drop an error silently. `let _` is also clippy's own suggested fix
for `unused_result_ok`, which is why it's banned too. Sometimes dropping is right, such as a send
whose receiver may already be gone. Then say so with an `#[expect]`. An `.ok()` used as a value, as
in `find` above, slips past both lints, so review catches that one.

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
  not matched on.
- **The cause is kept.** `map_err(|_| …)` replaces the real cause (an `io::Error`, a parse error)
  with your own error and throws the original away. Wrap it with `#[source]` or `#[from]` so the
  chain survives. A public function's error never exposes a dependency's error type directly,
  because then every caller depends on that library too.
- **`anyhow` and `eyre` stay where errors only get printed:** `main`, a CLI command, a test. In a
  library, they hide the error's type, so callers can print it but can't match on it. The `Result`
  aliases are listed separately because banning `anyhow::Error` doesn't catch `anyhow::Result<T>`. A
  binary crate's own `clippy.toml` leaves these four entries out. At the process boundary, add
  `.context(...)` so the printed chain says what was being attempted.
- **Errors derive `Clone, PartialEq, Eq`** so tests can `assert_eq!` on them, unless a cause can't
  (`io::Error` has none of them).
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
| `disallowed-methods`: `catch_unwind` | catching a panic to recover from it |
| `cast_possible_truncation`, `cast_sign_loss`, `cast_possible_wrap` | an `as` cast that truncates, drops the sign or wraps |
| `string_slice` | `&s[a..b]` on a `str` |
| clippy.toml: `allow-unwrap-in-tests`, `allow-expect-in-tests`, `allow-panic-in-tests` | lets tests do all of the above |

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
- `catch_unwind` is banned because recovering from panics is not error handling. It also does
  nothing when the binary is built with `panic = "abort"`.
- **An `as` cast between integers never fails, so it gets the value wrong instead.** `300u64 as u8`
  is `44`, `-1i64 as u64` is `18446744073709551615`, and `u64::MAX as i64` is `-1`. The three cast
  lints catch those casts. Use `From` when the conversion can't lose anything, and `TryFrom` when
  it can, so the error reaches the caller.
- **Slicing a `str` at a byte offset panics** when the offset lands inside a multi-byte character:
  `&"aé123"[..2]` panics, because `é` takes two bytes. `string_slice` catches `&s[a..b]`. Nothing
  catches `split_at`, so review does. Use `split_once`, `char_indices` or `s.get(a..b)`, which
  returns `None` instead of panicking.
- **Arithmetic that can overflow panics in a debug build and wraps in release.** For money and
  quantities, both are wrong: `cents * percent` can overflow on a large order. Use `checked_mul` and
  friends and return an error. Clippy's lint for this, `arithmetic_side_effects`, flags every `+`
  and `*`, which is too noisy to enable, so review catches it.

In a test, a panic is how the test fails, so unwrapping there is the assertion. The three
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
up or to clone. Asking for more than the function uses costs every caller. So take `&T` when you
only read, and `Option<&T>` rather than `&Option<T>`, which any caller can produce, even one that
holds a `T` and no `Option`. Clippy already flags `&String`, `&Vec` and `&Box` parameters by
default. A clone whose original is never used again is pure cost: move the value instead.

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

If a function reads the clock or a random generator inside, its signature lies. It looks like the
same inputs always give the same output, but they don't.

```rust
// Untestable: "the day the trial expires" can't be reached without waiting for it.
fn is_expired(&self) -> bool { Utc::now() > self.expires_at }

// Time is just a value: a test picks the moment it needs.
fn is_expired(&self, now: DateTime<Utc>) -> bool { now > self.expires_at }
```

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

**Review checks two more things:**

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

  A future dropped at an `.await` must not leave an effect half done. How to make it safe, by
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
  `LoadOrders` names the job.
- **A trait needs a second implementation or a test double.** A trait with one implementation adds
  a name and an indirection that every reader has to step through, and it hides which code
  actually runs, all for flexibility nobody uses yet. Write the concrete type first. Extract the
  trait when a second implementation, or a test double standing in for the network, disk or
  clock, actually needs it.
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
- **Where a law exists, a property test replaces examples.** A type with `Display` and `FromStr` has
  one that its printed form parses back:

  ```rust
  proptest! {
      #[test]
      fn port_display_parses_back(n in 1u16..) {
          let port = Port::try_from(n)?;
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
| `Eq` is a promise the compiler can't check | Reflexivity spelled out, and `Eq` only by derive (section 3) |

The same review also adopted one point from a video walkthrough of Google's guide, the presenter's
own preference rather than Google's rule: `Option` means absence and `Result` means failure. A
constructor now returns `Result`, never `Option`, with an error holding only its own failures
(sections 4 and 6). Before that, this guide followed `NonZero::new` and allowed `Option` for one
self-evident failure.

**Already here, often more strictly:** an enum instead of a bool parameter, a newtype instead of a
type alias, pattern matching instead of check-then-unwrap, borrowing instead of cloning, a
`SAFETY:` comment on `unsafe`, and a trait only for a second implementation or a test double.

**Kept against Google, on purpose:**

- **`Eq` wherever it holds.** Google prefers `PartialEq` alone, because adding `Eq` to a published
  type is a promise that is hard to take back. Here, domain types need `Eq` to be map keys, and the
  derive can't be wrong (section 3). A crate published for others to depend on may drop the lint and
  add `Eq` only where it means to promise it.
- **No `panic!` for broken invariants.** Google allows it. This guide makes functions total
  (section 8), which Google itself notes some codebases do.
- **`Arc` is fine.** Google's "avoid `Rc` and `Arc`" fits Chromium's threading model. An async
  backend shares state across tasks with `Arc`.

**Not taken:** required `#[must_use]` (`Result` is already must-use, and the lint is noisy), required
doc comments (too noisy for application code), extra type annotations, and `format!` instead of
`+`.

## Settings that only make the files work

- **`allow-invalid = true`** on library paths (`anyhow`, `chrono`, `rand`, `uuid`) keeps an entry
  quiet in a crate that doesn't depend on that library. Without it, clippy warns that the path
  doesn't resolve, and the same file couldn't serve every crate.
- **Entries marked "domain crates only" or "library crates only"** are left out of the copy of
  `clippy.toml` in crates where they don't apply. A binary prints `anyhow` errors and reads the
  clock, and an infrastructure crate holds locks.

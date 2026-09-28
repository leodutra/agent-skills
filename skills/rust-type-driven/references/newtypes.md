# Newtypes: serde, clap, databases, std traits, and a template

Read with the Newtypes section of SKILL.md, which says which constructor to write, what to name it,
and what a refinement may expose. This file says how a refinement meets the rest of the ecosystem,
and ends with a template that passes the skill's lints. A lint named after a rule holds
it (Enforce with Tools); the rest is review's. A refinement's error follows SKILL.md, Error
Modeling.

## serde

- A refinement deserializes through its constructor:
  `#[serde(try_from = "String", into = "String")]` (or `"u16"`, and so on), backed by
  `TryFrom<Inner>` and `From<Self> for Inner`. A bad value then fails deserialization with the
  constructor's own message.
- A tag MAY use `#[serde(transparent)]`: it has no invariant to skip.
- A closed set is an enum with `#[serde(rename_all = "kebab-case")]`, not a refinement over a
  string.

## clap (derive)

- A field of a type with `FromStr + Clone + Send + Sync + 'static` is parsed through `FromStr` with
  no further glue: `#[arg(long)] email: Email`. A custom `value_parser` is not written.
- `default_value_t = CONST` prints the constant with `Display` and parses it back through
  `FromStr`, so `Display` must round-trip (Testing Strategy: a property test holds it).
- `env = "VAR"`, `Vec<T>` with `value_delimiter = ','`, and `Option<T>` work unchanged.
- A closed set is a `#[derive(ValueEnum)]` enum, not `FromStr`: it gets the choices in the help
  text and in completions.

## Databases (sqlx, diesel)

- A refinement never has `#[sqlx(transparent)]`: decoding builds it without the constructor.
- `Decode` (sqlx) or `FromSql` (diesel) decodes the inner type, then calls `T::try_from(inner)`
  and maps the error. `Encode` or `ToSql` may delegate to the inner type.

## std traits

- Every newtype provides `Debug, Clone, PartialEq, Eq, Hash` (clippy:
  `missing_debug_implementations`, `derive_partial_eq_without_eq`); `Copy` when the inner
  type is `Copy`; `PartialOrd` and `Ord` when an order means something.
- `Display` when there is a canonical text form: `FromStr` and clap's defaults invert it.
- `AsRef<str>`, and `Borrow<str>` only when `Eq`, `Hash` and `Ord` agree with the inner type's,
  which a derive over the single field guarantees; it lets `set.contains("x")` work.
- `PartialEq<str>` and `PartialEq<&str>`, for plain comparisons in tests.
- A secret hand-writes a redacted `Debug`, has no `Display`, and no `Serialize` unless it is
  required.

## Template

Two refinements, one per failure shape: `Email`, several reasons, so `Result` and an error enum;
`Port`, one self-evident failure on top of std's `NonZeroU16`, so `Option`. Then the edge that
parses both. The skill's repository checks it with `cargo fmt` and the skill's lints.

```rust
// src/domain/email.rs
use std::{borrow::Borrow, fmt, str::FromStr};

// A refinement: the field is private, and serde goes through TryFrom<String>, so through new().
#[derive(
    Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, serde::Serialize, serde::Deserialize,
)]
#[serde(try_from = "String", into = "String")]
pub struct Email(String);

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
#[non_exhaustive]
pub enum EmailError {
    #[error("email is empty")]
    Empty,
    #[error("email is missing '@'")]
    MissingAt,
    #[error("email exceeds {max} bytes")]
    TooLong { max: usize },
}

impl Email {
    pub const MAX_LEN: usize = 254;

    /// The one validating path: FromStr, TryFrom<String>, serde and clap all come here.
    pub fn new(raw: impl Into<String>) -> Result<Self, EmailError> {
        let raw = raw.into();
        // Normalized first, so Eq, Hash and Ord compare canonical values; an already trimmed String is kept.
        let value = if raw.trim().len() == raw.len() {
            raw
        } else {
            raw.trim().to_owned()
        };
        if value.is_empty() {
            return Err(EmailError::Empty);
        }
        if value.len() > Self::MAX_LEN {
            return Err(EmailError::TooLong { max: Self::MAX_LEN });
        }
        if !value.contains('@') {
            return Err(EmailError::MissingAt);
        }
        Ok(Self(value))
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }

    #[must_use]
    pub fn into_inner(self) -> String {
        self.0
    }
}

impl FromStr for Email {
    type Err = EmailError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        Self::new(s)
    }
}

impl TryFrom<String> for Email {
    type Error = EmailError;

    fn try_from(s: String) -> Result<Self, Self::Error> {
        Self::new(s)
    }
}

impl From<Email> for String {
    fn from(email: Email) -> Self {
        email.0
    }
}

impl AsRef<str> for Email {
    fn as_ref(&self) -> &str {
        &self.0
    }
}

// Eq, Hash and Ord are derived on the one field, so they agree with str's, as Borrow requires.
impl Borrow<str> for Email {
    fn borrow(&self) -> &str {
        &self.0
    }
}

impl PartialEq<str> for Email {
    fn eq(&self, other: &str) -> bool {
        self.0 == other
    }
}

impl PartialEq<&str> for Email {
    fn eq(&self, other: &&str) -> bool {
        self.0 == *other
    }
}

impl fmt::Display for Email {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.0)
    }
}
```

```rust
// src/domain/port.rs
use std::{fmt, num::NonZeroU16, num::ParseIntError, str::FromStr};

// A refinement on std's NonZeroU16: the invariant is the inner type's, and Option<Port> is 2 bytes.
#[derive(
    Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, serde::Serialize, serde::Deserialize,
)]
#[serde(try_from = "u16", into = "u16")]
pub struct Port(NonZeroU16);

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum PortError {
    #[error("port must be non-zero")]
    Zero,
    #[error("invalid port number: {0}")]
    Syntax(#[from] ParseIntError),
}

impl Port {
    /// The one validating path. One self-evident failure, zero, so it returns Option.
    #[must_use]
    pub const fn new(n: u16) -> Option<Self> {
        match NonZeroU16::new(n) {
            Some(n) => Some(Self(n)),
            None => None,
        }
    }

    /// Literals only: called in a const item, an invalid value fails compilation.
    #[must_use]
    #[expect(
        clippy::panic,
        reason = "a compile-time literal: an invalid value fails compilation"
    )]
    pub const fn literal(n: u16) -> Self {
        match Self::new(n) {
            Some(port) => port,
            None => panic!("port must be non-zero"),
        }
    }

    #[must_use]
    pub const fn get(self) -> u16 {
        self.0.get()
    }
}

impl TryFrom<u16> for Port {
    type Error = PortError;

    fn try_from(n: u16) -> Result<Self, Self::Error> {
        Self::new(n).ok_or(PortError::Zero)
    }
}

impl From<Port> for u16 {
    fn from(port: Port) -> Self {
        port.get()
    }
}

impl FromStr for Port {
    type Err = PortError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        s.parse::<u16>()?.try_into()
    }
}

impl fmt::Display for Port {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.0.fmt(f)
    }
}

pub const HTTP: Port = Port::literal(80);
```

```rust
// src/cli.rs
// The edge. clap parses each field through FromStr, so no value_parser is written.
use crate::domain::email::Email;
use crate::domain::port::{self, Port};

#[derive(Debug, clap::Parser)]
pub struct Cli {
    #[arg(long, env = "APP_EMAIL")]
    pub email: Email,
    // default_value_t prints the default with Display and parses it back through FromStr.
    #[arg(long, default_value_t = port::HTTP)]
    pub port: Port,
    #[arg(long, value_delimiter = ',')]
    pub cc: Vec<Email>,
}
```

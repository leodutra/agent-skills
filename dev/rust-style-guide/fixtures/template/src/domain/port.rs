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

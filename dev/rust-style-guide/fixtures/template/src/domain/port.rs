use std::{fmt, num::NonZeroU16, num::ParseIntError, str::FromStr};

// A refinement on std's NonZeroU16: the invariant is the inner type's, and Option<Port> is 2 bytes.
#[derive(
    Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, serde::Serialize, serde::Deserialize,
)]
#[serde(try_from = "u16", into = "u16")]
pub struct Port(NonZeroU16);

/// The constructor's only failure, so a unit struct.
#[derive(Debug, Clone, Copy, PartialEq, Eq, thiserror::Error)]
#[error("port must be non-zero")]
pub struct ZeroPort;

/// Text adds a syntax failure in front of the constructor's.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ParsePortError {
    #[error("invalid port number: {0}")]
    Syntax(#[from] ParseIntError),
    #[error(transparent)]
    Zero(#[from] ZeroPort),
}

impl Port {
    /// The one validating path. A failure is an error, not absence, so it returns Result.
    pub const fn new(n: u16) -> Result<Self, ZeroPort> {
        match NonZeroU16::new(n) {
            Some(n) => Ok(Self(n)),
            None => Err(ZeroPort),
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
            Ok(port) => port,
            Err(ZeroPort) => panic!("port must be non-zero"),
        }
    }

    #[must_use]
    pub const fn get(self) -> u16 {
        self.0.get()
    }
}

impl TryFrom<u16> for Port {
    type Error = ZeroPort;

    fn try_from(n: u16) -> Result<Self, Self::Error> {
        Self::new(n)
    }
}

impl From<Port> for u16 {
    fn from(port: Port) -> Self {
        port.get()
    }
}

impl FromStr for Port {
    type Err = ParsePortError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        Ok(Self::new(s.parse()?)?)
    }
}

impl fmt::Display for Port {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.0.fmt(f)
    }
}

pub const HTTP: Port = Port::literal(80);

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn each_source_reports_only_its_own_failures() {
        assert_eq!(Port::new(0), Err(ZeroPort));
        assert_eq!("0".parse::<Port>(), Err(ParsePortError::Zero(ZeroPort)));
        assert!(matches!(
            "x".parse::<Port>(),
            Err(ParsePortError::Syntax(_))
        ));
        assert_eq!(HTTP.to_string().parse::<Port>(), Ok(HTTP));
    }
}

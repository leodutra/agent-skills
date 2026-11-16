use std::{fmt, num::NonZeroU16, str::FromStr};

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Port(NonZeroU16);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct InvalidPort;

impl FromStr for Port {
    type Err = InvalidPort;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        s.parse::<NonZeroU16>().map(Self).map_err(|_e| InvalidPort)
    }
}

impl fmt::Display for Port {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "port {}", self.0)
    }
}

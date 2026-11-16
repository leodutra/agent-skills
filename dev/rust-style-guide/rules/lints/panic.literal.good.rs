// Allowed: literal's panic in const items, under its #[expect].
use std::num::NonZeroU16;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Port(NonZeroU16);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ZeroPort;

impl Port {
    /// # Errors
    /// [`ZeroPort`] when `n` is 0.
    pub const fn try_new(n: u16) -> Result<Self, ZeroPort> {
        match NonZeroU16::new(n) {
            Some(n) => Ok(Self(n)),
            None => Err(ZeroPort),
        }
    }

    #[must_use]
    #[expect(clippy::panic, reason = "a compile-time literal: an invalid value fails compilation")]
    pub(crate) const fn literal(n: u16) -> Self {
        match Self::try_new(n) {
            Ok(port) => port,
            Err(ZeroPort) => panic!("port must be non-zero"),
        }
    }
}

pub const HTTP: Port = Port::literal(80);

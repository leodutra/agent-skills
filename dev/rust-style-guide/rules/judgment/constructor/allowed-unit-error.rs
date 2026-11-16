// keep: the ZeroQuantity unit-struct error
use std::num::NonZeroU32;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Quantity(NonZeroU32);

/// The constructor's only failure.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ZeroQuantity;

impl Quantity {
    /// # Errors
    /// [`ZeroQuantity`] when `n` is 0.
    pub const fn try_new(n: u32) -> Result<Self, ZeroQuantity> {
        match NonZeroU32::new(n) {
            Some(n) => Ok(Self(n)),
            None => Err(ZeroQuantity),
        }
    }
}

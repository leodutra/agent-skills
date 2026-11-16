use std::num::TryFromIntError;

/// # Errors
/// When `n` does not fit in a `u32`.
pub fn low(n: u64) -> Result<u32, TryFromIntError> {
    u32::try_from(n)
}

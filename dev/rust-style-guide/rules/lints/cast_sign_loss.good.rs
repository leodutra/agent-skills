use std::num::TryFromIntError;

/// # Errors
/// When `n` is negative.
pub fn unsigned(n: i64) -> Result<u64, TryFromIntError> {
    u64::try_from(n)
}

use std::num::TryFromIntError;

/// # Errors
/// When `n` is above `i64::MAX`.
pub fn signed(n: u64) -> Result<i64, TryFromIntError> {
    i64::try_from(n)
}

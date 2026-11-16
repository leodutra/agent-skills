use std::num::ParseIntError;

/// # Errors
/// The parse error when `s` is not a number.
pub fn count(s: &str) -> Result<u32, ParseIntError> {
    s.parse()
}

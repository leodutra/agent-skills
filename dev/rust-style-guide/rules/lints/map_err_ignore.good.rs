use std::num::ParseIntError;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CountError {
    Syntax(ParseIntError),
}

/// # Errors
/// [`CountError::Syntax`] when `s` is not a number.
pub fn count(s: &str) -> Result<u32, CountError> {
    s.parse().map_err(CountError::Syntax)
}

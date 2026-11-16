use std::num::ParseIntError;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum RetryConfigError {
    #[error("invalid retry count")]
    Count(#[source] ParseIntError),
}

/// # Errors
/// [`RetryConfigError::Count`] when `raw` isn't a number.
pub fn retries(raw: &str) -> Result<u8, RetryConfigError> {
    raw.trim().parse().map_err(RetryConfigError::Count)
}

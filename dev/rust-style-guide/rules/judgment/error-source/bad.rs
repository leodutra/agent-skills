#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum RetryConfigError {
    #[error("invalid retry count: {0}")]
    Count(String),
}

/// # Errors
/// [`RetryConfigError::Count`] when `raw` isn't a number.
pub fn retries(raw: &str) -> Result<u8, RetryConfigError> {
    raw.trim().parse().map_err(|e: std::num::ParseIntError| RetryConfigError::Count(e.to_string()))
}

// expect: clippy::map_err_ignore
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BadCount;

/// # Errors
/// [`BadCount`] when `s` is not a number.
pub fn count(s: &str) -> Result<u32, BadCount> {
    s.parse().map_err(|_| BadCount)
}

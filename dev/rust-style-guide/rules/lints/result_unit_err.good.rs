#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct OverHundred;

/// # Errors
/// [`OverHundred`] when `n` is above 100.
pub const fn percent(n: u8) -> Result<u8, OverHundred> {
    if n <= 100 { Ok(n) } else { Err(OverHundred) }
}

// expect: clippy::disallowed_types anyhow::Error
/// # Errors
/// When `s` is not a number.
pub fn count(s: &str) -> Result<u32, anyhow::Error> {
    Ok(s.parse()?)
}

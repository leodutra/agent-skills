// expect: clippy::disallowed_types anyhow::Result
/// # Errors
/// When `s` is not a number.
pub fn count(s: &str) -> anyhow::Result<u32> {
    Ok(s.parse()?)
}

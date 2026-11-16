// expect: clippy::disallowed_types eyre::Result
/// # Errors
/// When `s` is not a number.
pub fn count(s: &str) -> eyre::Result<u32> {
    Ok(s.parse()?)
}

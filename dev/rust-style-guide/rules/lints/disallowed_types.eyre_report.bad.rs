// expect: clippy::disallowed_types eyre::Report
/// # Errors
/// When `s` is not a number.
pub fn count(s: &str) -> Result<u32, eyre::Report> {
    Ok(s.parse()?)
}

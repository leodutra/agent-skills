// expect: clippy::allow_attributes
#[allow(clippy::unwrap_used, reason = "the literal always parses")]
#[must_use]
pub fn answer() -> u32 {
    "42".parse().unwrap()
}

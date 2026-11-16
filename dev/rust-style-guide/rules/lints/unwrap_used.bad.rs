// expect: clippy::unwrap_used
#[must_use]
pub fn count(s: &str) -> u32 {
    s.parse().unwrap()
}

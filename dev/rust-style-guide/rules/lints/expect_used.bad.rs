// expect: clippy::expect_used
#[must_use]
pub fn count(s: &str) -> u32 {
    s.parse().expect("a number")
}

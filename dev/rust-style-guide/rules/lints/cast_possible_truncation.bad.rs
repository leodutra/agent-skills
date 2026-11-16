// expect: clippy::cast_possible_truncation
#[must_use]
pub const fn low(n: u64) -> u32 {
    n as u32
}

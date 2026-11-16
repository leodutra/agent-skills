// expect: clippy::cast_possible_wrap
#[must_use]
pub const fn signed(n: u64) -> i64 {
    n as i64
}

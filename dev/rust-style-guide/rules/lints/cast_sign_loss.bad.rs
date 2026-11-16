// expect: clippy::cast_sign_loss
#[must_use]
pub const fn unsigned(n: i64) -> u64 {
    n as u64
}

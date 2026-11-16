#[must_use]
pub const fn parity(n: u32) -> &'static str {
    if n.is_multiple_of(2) { "even" } else { "odd" }
}

#[must_use]
pub const fn ratio(n: u32, d: u32) -> Option<u32> {
    n.checked_div(d)
}

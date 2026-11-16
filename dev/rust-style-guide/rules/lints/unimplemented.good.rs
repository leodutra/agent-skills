#[must_use]
pub const fn fee(cents: u64) -> u64 {
    cents / 100
}

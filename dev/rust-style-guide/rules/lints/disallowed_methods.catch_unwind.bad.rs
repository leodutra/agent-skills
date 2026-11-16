// expect: clippy::disallowed_methods std::panic::catch_unwind
#[must_use]
pub fn guarded(n: u32) -> Option<u32> {
    std::panic::catch_unwind(|| n.saturating_mul(2)).ok()
}

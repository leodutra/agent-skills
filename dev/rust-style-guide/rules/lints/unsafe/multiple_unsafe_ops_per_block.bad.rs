// expect: clippy::multiple_unsafe_ops_per_block
#[expect(unsafe_code, reason = "probe: the unsafe lints need unsafe code")]
#[must_use]
pub fn ends(bytes: &[u8; 4]) -> (u8, u8) {
    // SAFETY: the array has four elements, so indices 0 and 3 are in bounds.
    unsafe { (*bytes.get_unchecked(0), *bytes.get_unchecked(3)) }
}

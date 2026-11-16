#[expect(unsafe_code, reason = "probe: the unsafe lints need unsafe code")]
#[must_use]
pub fn first(bytes: &[u8; 4]) -> u8 {
    // SAFETY: the array has four elements, so index 0 is in bounds.
    unsafe { *bytes.get_unchecked(0) }
}

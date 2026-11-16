#[expect(unsafe_code, reason = "probe: the unsafe lints need unsafe code")]
#[must_use]
pub fn ends(bytes: &[u8; 4]) -> (u8, u8) {
    // SAFETY: the array has four elements, so index 0 is in bounds.
    let first = unsafe { *bytes.get_unchecked(0) };
    // SAFETY: the array has four elements, so index 3 is in bounds.
    let last = unsafe { *bytes.get_unchecked(3) };
    (first, last)
}

/// # Safety
/// `index` must be below 4.
#[expect(unsafe_code, reason = "probe: the unsafe lints need unsafe code")]
#[must_use]
pub unsafe fn at(bytes: &[u8; 4], index: usize) -> u8 {
    // SAFETY: the caller guarantees `index < 4`, the array's length.
    unsafe { *bytes.get_unchecked(index) }
}

/// The first byte of a buffer the caller owns.
///
/// # Safety
/// `buffer` must point to at least one readable byte.
#[expect(unsafe_code, reason = "probe: the unsafe lints need unsafe code")]
#[must_use]
pub unsafe fn first_byte(buffer: *const u8) -> u8 {
    // SAFETY: the caller guarantees `buffer` points to a readable byte.
    unsafe { *buffer }
}

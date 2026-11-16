// expect: clippy::not_unsafe_ptr_arg_deref
/// The first byte of a buffer the caller owns.
#[expect(unsafe_code, reason = "probe: the unsafe lints need unsafe code")]
#[must_use]
pub fn first_byte(buffer: *const u8) -> u8 {
    // SAFETY: callers pass a pointer to at least one readable byte.
    unsafe { *buffer }
}

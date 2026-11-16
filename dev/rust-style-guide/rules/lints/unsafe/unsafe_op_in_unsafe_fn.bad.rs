// expect: unsafe_op_in_unsafe_fn
/// # Safety
/// `index` must be below 4.
#[expect(unsafe_code, reason = "probe: the unsafe lints need unsafe code")]
#[must_use]
pub unsafe fn at(bytes: &[u8; 4], index: usize) -> u8 {
    *bytes.get_unchecked(index)
}

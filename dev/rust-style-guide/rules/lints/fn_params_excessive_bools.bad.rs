// expect: clippy::fn_params_excessive_bools
#[must_use]
pub const fn flags(bold: bool, italic: bool, underline: bool, strike: bool) -> u8 {
    bold as u8 | (italic as u8) << 1 | (underline as u8) << 2 | (strike as u8) << 3
}

// expect: clippy::unnecessary_wraps
pub fn doubled(n: u8) -> Option<u16> {
    Some(u16::from(n) * 2)
}

// expect: clippy::unreachable
#[must_use]
pub fn parity(n: u32) -> &'static str {
    match n % 2 {
        0 => "even",
        1 => "odd",
        _ => unreachable!(),
    }
}

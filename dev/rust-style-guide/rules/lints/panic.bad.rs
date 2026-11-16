// expect: clippy::panic
#[must_use]
pub fn ratio(n: u32, d: u32) -> u32 {
    if d == 0 {
        panic!("zero divisor");
    }
    n / d
}

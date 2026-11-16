// expect: clippy::disallowed_methods rand::rng
use rand::Rng;

#[must_use]
pub fn die() -> u8 {
    rand::rng().random_range(1..=6)
}

// expect: clippy::disallowed_methods rand::thread_rng
// also: deprecated
use rand::Rng;

#[must_use]
pub fn die() -> u8 {
    rand::thread_rng().random_range(1..=6)
}

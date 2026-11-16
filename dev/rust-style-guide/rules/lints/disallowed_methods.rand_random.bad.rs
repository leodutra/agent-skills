// expect: clippy::disallowed_methods rand::random
#[must_use]
pub fn coin() -> bool {
    rand::random()
}

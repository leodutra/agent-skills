#[must_use]
pub fn initials(name: &str) -> Option<&str> {
    name.get(0..2)
}

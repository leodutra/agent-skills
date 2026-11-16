// expect: clippy::string_slice
#[must_use]
pub fn initials(name: &str) -> &str {
    &name[0..2]
}

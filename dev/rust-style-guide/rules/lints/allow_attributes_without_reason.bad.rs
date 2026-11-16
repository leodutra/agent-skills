// expect: clippy::allow_attributes_without_reason
#[expect(clippy::unwrap_used)]
#[must_use]
pub fn answer() -> u32 {
    "42".parse().unwrap()
}

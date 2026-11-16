// expect: clippy::needless_pass_by_value
#[must_use]
pub fn shout(text: String) -> String {
    text.to_uppercase()
}

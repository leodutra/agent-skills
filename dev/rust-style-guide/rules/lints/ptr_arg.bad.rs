// expect: clippy::ptr_arg
#[must_use]
pub fn shout(text: &String) -> String {
    text.to_uppercase()
}

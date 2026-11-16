// expect: clippy::ref_option
#[must_use]
pub fn greeting(name: &Option<String>) -> String {
    match name {
        Some(name) => format!("hello, {name}"),
        None => "hello".to_owned(),
    }
}

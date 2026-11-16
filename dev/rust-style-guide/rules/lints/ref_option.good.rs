#[must_use]
pub fn greeting(name: Option<&str>) -> String {
    match name {
        Some(name) => format!("hello, {name}"),
        None => "hello".to_owned(),
    }
}

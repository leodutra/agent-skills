// expect: clippy::redundant_clone
#[must_use]
pub fn titled(name: &str) -> String {
    let title = format!("Dr. {name}");
    title.clone()
}

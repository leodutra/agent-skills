// expect: clippy::borrowed_box
#[must_use]
pub fn length(items: &Box<[u32]>) -> usize {
    items.len()
}

// expect: clippy::dbg_macro
#[must_use]
pub fn total(items: &[u32]) -> u32 {
    dbg!(items.iter().sum())
}

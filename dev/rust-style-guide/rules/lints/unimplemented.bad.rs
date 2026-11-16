// expect: clippy::unimplemented
#[must_use]
pub fn fee(_cents: u64) -> u64 {
    unimplemented!()
}

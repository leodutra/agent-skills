// expect: clippy::new_without_default
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Tally {
    count: u32,
}

impl Tally {
    #[must_use]
    pub const fn new() -> Self {
        Self { count: 0 }
    }
}

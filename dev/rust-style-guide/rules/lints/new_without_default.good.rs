#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct Tally {
    count: u32,
}

impl Tally {
    #[must_use]
    pub const fn count(&self) -> u32 {
        self.count
    }
}

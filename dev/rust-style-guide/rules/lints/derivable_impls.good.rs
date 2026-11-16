#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct Retries {
    count: u8,
}

impl Retries {
    #[must_use]
    pub const fn count(self) -> u8 {
        self.count
    }
}

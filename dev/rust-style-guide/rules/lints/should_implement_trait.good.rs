#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Cents(pub u64);

impl Cents {
    /// Adds, stopping at `u64::MAX` cents.
    #[must_use]
    pub const fn saturating_add(self, other: Self) -> Self {
        Self(self.0.saturating_add(other.0))
    }
}

// expect: clippy::should_implement_trait
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Cents(pub u64);

impl Cents {
    #[must_use]
    pub fn add(self, other: Self) -> Self {
        Self(self.0.saturating_add(other.0))
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Customer {
    name: String,
}

impl Customer {
    #[must_use]
    pub const fn new(name: String) -> Self {
        Self { name }
    }

    /// Callers only print or compare it.
    #[must_use]
    pub fn name(&self) -> String {
        self.name.clone()
    }
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Price {
    pub dollars: f64,
}

impl Price {
    /// The price with sales tax added, `rate` as a fraction (0.0825 for 8.25%).
    #[must_use]
    pub fn with_tax(self, rate: f64) -> Self {
        Self { dollars: self.dollars * (1.0 + rate) }
    }
}

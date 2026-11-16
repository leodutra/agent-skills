#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct Price {
    pub cents: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct PriceOverflow;

impl Price {
    /// The price with sales tax added, `basis_points` per 10 000 (825 for 8.25%), rounded half up.
    ///
    /// # Errors
    /// [`PriceOverflow`] when the taxed price doesn't fit in a `u64`.
    pub fn with_tax(self, basis_points: u32) -> Result<Self, PriceOverflow> {
        let tax = self.cents.checked_mul(u64::from(basis_points)).ok_or(PriceOverflow)?;
        let cents = self.cents.checked_add(tax.div_ceil(10_000)).ok_or(PriceOverflow)?;
        Ok(Self { cents })
    }
}

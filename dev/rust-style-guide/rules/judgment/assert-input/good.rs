#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CartLine {
    quantity: u32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct QuantityOutOfRange;

impl CartLine {
    /// Sets the quantity the customer typed in the cart.
    ///
    /// # Errors
    /// [`QuantityOutOfRange`] unless `quantity` is 1 to 99.
    pub fn set_quantity(&mut self, quantity: u32) -> Result<(), QuantityOutOfRange> {
        if !(1..=99).contains(&quantity) {
            return Err(QuantityOutOfRange);
        }
        self.quantity = quantity;
        Ok(())
    }
}

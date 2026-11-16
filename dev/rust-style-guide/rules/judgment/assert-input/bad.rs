#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CartLine {
    quantity: u32,
}

impl CartLine {
    /// Sets the quantity the customer typed in the cart.
    pub fn set_quantity(&mut self, quantity: u32) {
        assert!((1..=99).contains(&quantity), "quantity must be 1 to 99");
        self.quantity = quantity;
    }
}

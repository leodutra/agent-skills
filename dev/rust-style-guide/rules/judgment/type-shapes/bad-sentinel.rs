#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Customer {
    pub name: String,
    /// Empty when the customer has no middle name.
    pub middle_name: String,
}

/// The position of `sku` in the cart, or -1 when it isn't there.
#[must_use]
pub fn position(cart: &[String], sku: &str) -> i64 {
    cart.iter().position(|item| item == sku).and_then(|i| i64::try_from(i).ok()).unwrap_or(-1)
}

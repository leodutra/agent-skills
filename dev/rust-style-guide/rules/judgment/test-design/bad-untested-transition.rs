#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OrderState {
    Placed,
    Shipped,
    Cancelled,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct InvalidTransition {
    pub from: OrderState,
}

impl OrderState {
    /// # Errors
    /// [`InvalidTransition`] unless the order is placed.
    pub const fn ship(self) -> Result<Self, InvalidTransition> {
        match self {
            Self::Placed => Ok(Self::Shipped),
            Self::Shipped | Self::Cancelled => Err(InvalidTransition { from: self }),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ships_a_placed_order() {
        assert_eq!(OrderState::Placed.ship(), Ok(OrderState::Shipped));
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Order {
    Placed,
    Shipped { tracking: String },
}

impl Order {
    /// Shipping always records the carrier's tracking number.
    pub fn ship(&mut self, tracking: String) {
        *self = Self::Shipped { tracking };
    }

    /// The line printed on the packing slip.
    #[must_use]
    pub fn slip_line(&self) -> String {
        match self {
            Self::Placed => "not shipped yet".to_owned(),
            Self::Shipped { tracking } => format!("tracking {tracking}"),
        }
    }
}

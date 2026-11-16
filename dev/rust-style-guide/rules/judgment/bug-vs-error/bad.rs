#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Status {
    Placed,
    Shipped,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Order {
    status: Status,
    tracking: Option<String>,
}

impl Order {
    #[must_use]
    pub const fn placed() -> Self {
        Self { status: Status::Placed, tracking: None }
    }

    /// Shipping always records the carrier's tracking number.
    pub fn ship(&mut self, tracking: String) {
        self.status = Status::Shipped;
        self.tracking = Some(tracking);
    }

    /// The line printed on the packing slip.
    #[must_use]
    pub fn slip_line(&self) -> String {
        match self.status {
            Status::Placed => "not shipped yet".to_owned(),
            Status::Shipped => format!("tracking {}", self.tracking.clone().unwrap_or_default()),
        }
    }
}

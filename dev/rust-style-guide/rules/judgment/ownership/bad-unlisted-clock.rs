use std::time::Duration;
use tokio::time::Instant;

/// A trial (domain type): it expires 14 days after it starts.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Trial {
    started: Instant,
}

impl Trial {
    #[must_use]
    pub const fn new(started: Instant) -> Self {
        Self { started }
    }

    #[must_use]
    pub fn is_expired(&self) -> bool {
        Instant::now().duration_since(self.started) > Duration::from_secs(14 * 24 * 60 * 60)
    }
}

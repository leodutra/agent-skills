use std::time::Duration;
use tokio::time::Instant;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Customer {
    name: String,
}

impl Customer {
    #[must_use]
    pub fn name(&self) -> &str {
        &self.name
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct Cart {
    lines: Vec<u64>,
    items: u64,
}

impl Cart {
    pub const fn add_item(&mut self) {
        self.items = self.items.saturating_add(1);
    }

    #[must_use]
    pub fn total_cents(&self) -> u64 {
        self.lines.iter().fold(0_u64, |total, cents| total.saturating_add(*cents))
    }
}

/// A trial: the caller passes the current time in.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Trial {
    started: Instant,
}

impl Trial {
    #[must_use]
    pub fn is_expired(&self, now: Instant) -> bool {
        now.duration_since(self.started) > Duration::from_secs(14 * 24 * 60 * 60)
    }
}

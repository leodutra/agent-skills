use std::sync::atomic::{AtomicU64, Ordering};

/// A shopping cart (domain type).
#[derive(Debug, Default)]
pub struct Cart {
    items: AtomicU64,
}

impl Cart {
    pub fn add_item(&self) {
        self.items.fetch_add(1, Ordering::Relaxed);
    }

    #[must_use]
    pub fn items(&self) -> u64 {
        self.items.load(Ordering::Relaxed)
    }
}

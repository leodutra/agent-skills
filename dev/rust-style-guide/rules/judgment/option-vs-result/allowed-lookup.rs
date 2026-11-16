// keep: price_of returning Option<u64>
use std::collections::BTreeMap;

#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct PriceList {
    cents: BTreeMap<String, u64>,
}

impl PriceList {
    pub fn set(&mut self, sku: &str, cents: u64) {
        self.cents.insert(sku.to_owned(), cents);
    }

    /// The price of `sku`, if it is listed.
    #[must_use]
    pub fn price_of(&self, sku: &str) -> Option<u64> {
        self.cents.get(sku).copied()
    }
}

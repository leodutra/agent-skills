// expect: clippy::iter_over_hash_type
use std::collections::HashMap;

#[must_use]
pub fn payout_order(amounts: &HashMap<u32, u64>) -> Vec<u32> {
    let mut order = Vec::new();
    for id in amounts.keys() {
        order.push(*id);
    }
    order
}

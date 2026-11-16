use std::collections::BTreeMap;

#[must_use]
pub fn payout_order(amounts: &BTreeMap<u32, u64>) -> Vec<u32> {
    let mut order = Vec::new();
    for id in amounts.keys() {
        order.push(*id);
    }
    order
}

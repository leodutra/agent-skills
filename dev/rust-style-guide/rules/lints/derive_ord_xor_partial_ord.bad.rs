// expect: clippy::derive_ord_xor_partial_ord
// also: clippy::non_canonical_partial_ord_impl
use std::cmp::Ordering;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Ord)]
pub struct Priority(pub u8);

impl PartialOrd for Priority {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(other.0.cmp(&self.0))
    }
}

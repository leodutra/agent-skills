// expect: clippy::wildcard_imports
use std::collections::*;

#[must_use]
pub fn sorted(items: &[u32]) -> BTreeSet<u32> {
    items.iter().copied().collect()
}

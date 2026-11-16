// expect: clippy::disallowed_methods std::sync::PoisonError::into_inner
use std::sync::PoisonError;

#[must_use]
pub fn recover(poisoned: PoisonError<Vec<u32>>) -> Vec<u32> {
    poisoned.into_inner()
}

// expect: clippy::disallowed_methods std::sync::PoisonError::get_ref
use std::sync::PoisonError;

#[must_use]
pub fn peek(poisoned: &PoisonError<Vec<u32>>) -> usize {
    poisoned.get_ref().len()
}

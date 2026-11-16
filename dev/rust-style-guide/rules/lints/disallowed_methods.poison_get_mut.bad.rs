// expect: clippy::disallowed_methods std::sync::PoisonError::get_mut
use std::sync::PoisonError;

pub fn clear(poisoned: &mut PoisonError<Vec<u32>>) {
    poisoned.get_mut().clear();
}

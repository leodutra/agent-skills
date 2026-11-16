// expect: clippy::disallowed_methods std::time::Instant::now
use std::time::Instant;

#[must_use]
pub fn expired(deadline: Instant) -> bool {
    Instant::now() > deadline
}

// expect: clippy::disallowed_methods std::time::SystemTime::now
use std::time::SystemTime;

#[must_use]
pub fn expired(deadline: SystemTime) -> bool {
    SystemTime::now() > deadline
}

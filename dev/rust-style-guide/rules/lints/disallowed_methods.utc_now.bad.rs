// expect: clippy::disallowed_methods chrono::Utc::now
use chrono::{DateTime, Utc};

#[must_use]
pub fn expired(deadline: DateTime<Utc>) -> bool {
    Utc::now() > deadline
}

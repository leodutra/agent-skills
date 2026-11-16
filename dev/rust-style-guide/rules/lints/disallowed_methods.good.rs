use chrono::{DateTime, Utc};
use rand::Rng;
use uuid::{Timestamp, Uuid};

#[must_use]
pub fn expired(now: DateTime<Utc>, deadline: DateTime<Utc>) -> bool {
    now > deadline
}

pub fn die(rng: &mut impl Rng) -> u8 {
    rng.random_range(1..=6)
}

#[must_use]
pub fn request_id(at: Timestamp) -> Uuid {
    Uuid::new_v7(at)
}

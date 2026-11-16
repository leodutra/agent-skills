// expect: clippy::disallowed_methods uuid::Uuid::now_v7
use uuid::Uuid;

#[must_use]
pub fn request_id() -> Uuid {
    Uuid::now_v7()
}

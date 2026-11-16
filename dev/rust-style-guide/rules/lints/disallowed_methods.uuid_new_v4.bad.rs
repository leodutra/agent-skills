// expect: clippy::disallowed_methods uuid::Uuid::new_v4
use uuid::Uuid;

#[must_use]
pub fn request_id() -> Uuid {
    Uuid::new_v4()
}

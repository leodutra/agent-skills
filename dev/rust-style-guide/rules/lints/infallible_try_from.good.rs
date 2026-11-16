#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct UserId(pub u64);

impl From<u64> for UserId {
    fn from(id: u64) -> Self {
        Self(id)
    }
}

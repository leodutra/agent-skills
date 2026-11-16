// expect: clippy::infallible_try_from
use std::convert::Infallible;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct UserId(pub u64);

impl TryFrom<u64> for UserId {
    type Error = Infallible;

    fn try_from(id: u64) -> Result<Self, Self::Error> {
        Ok(Self(id))
    }
}

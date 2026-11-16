//! Tags: every `u64` is a valid id, so the field is `pub` (Allowed), and two types keep ids apart.
//!
//! Each `compile_fail` below has a twin that differs only in the misuse line and compiles, so a
//! typo can't pass for a rejection (stable rustdoc doesn't check `compile_fail`'s error code).
//!
//! An `OrderId` where a `UserId` belongs is rejected:
//! ```compile_fail
//! use template::domain::ids::{OrderId, UserId, is_system};
//! is_system(OrderId(0));
//! ```
//! ```
//! use template::domain::ids::{OrderId, UserId, is_system};
//! is_system(UserId(0));
//! ```
//! So is a bare `u64`: the function takes the newtype, never `impl Into<UserId>`:
//! ```compile_fail
//! use template::domain::ids::{UserId, is_system};
//! is_system(0);
//! ```
//! ```
//! use template::domain::ids::{UserId, is_system};
//! is_system(UserId(0));
//! ```

#[derive(
    Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, serde::Serialize, serde::Deserialize,
)]
#[serde(transparent)]
pub struct UserId(pub u64);

#[derive(
    Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, serde::Serialize, serde::Deserialize,
)]
#[serde(transparent)]
pub struct OrderId(pub u64);

impl From<u64> for UserId {
    fn from(id: u64) -> Self {
        Self(id)
    }
}

impl From<u64> for OrderId {
    fn from(id: u64) -> Self {
        Self(id)
    }
}

/// User 0 is the system account.
#[must_use]
pub const fn is_system(user: UserId) -> bool {
    user.0 == 0
}

// keep: the UserId and OrderId newtypes with their pub fields
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct UserId(pub u64);

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct OrderId(pub u64);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Cancellation {
    pub by: UserId,
    pub order: OrderId,
}

#[must_use]
pub const fn cancel(by: UserId, order: OrderId) -> Cancellation {
    Cancellation { by, order }
}

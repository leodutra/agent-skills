use std::marker::PhantomData;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Paid;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Shipped;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Order<State> {
    id: u64,
    state: PhantomData<State>,
}

impl<State> Order<State> {
    #[must_use]
    pub const fn id(&self) -> u64 {
        self.id
    }
}

impl Order<Paid> {
    #[must_use]
    pub const fn ship(self) -> Order<Shipped> {
        Order { id: self.id, state: PhantomData }
    }
}

/// Loads an order from its database row; every order the dispatcher loads has been paid.
#[must_use]
pub const fn load_for_dispatch(id: u64) -> Order<Paid> {
    Order { id, state: PhantomData }
}

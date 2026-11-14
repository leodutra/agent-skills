//! Reservations: holding stock in a warehouse for a customer's order until it ships.
use std::collections::{BTreeMap, BTreeSet};

/// An order as checkout hands it over. Ids come from database sequences; any value is valid.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Order {
    pub id: u64,
    pub customer_id: u64,
    pub warehouse_id: u64,
}

/// Stock held for one order.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Reservation {
    pub order_id: u64,
    pub customer_id: u64,
    pub warehouse_id: u64,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ReserveError {
    #[error("order {order_id} already holds a reservation")]
    AlreadyReserved { order_id: u64 },
    #[error("customer {customer_id} has no account")]
    UnknownCustomer { customer_id: u64 },
}

#[derive(Debug, Default)]
pub struct Reservations {
    customers: BTreeSet<u64>,
    by_order: BTreeMap<u64, Reservation>,
}

impl Reservations {
    pub fn add_customer(&mut self, customer_id: u64) {
        self.customers.insert(customer_id);
    }

    pub fn reserve(
        &mut self,
        customer_id: u64,
        order_id: u64,
        warehouse_id: u64,
    ) -> Result<&Reservation, ReserveError> {
        if !self.customers.contains(&customer_id) {
            return Err(ReserveError::UnknownCustomer { customer_id });
        }
        match self.by_order.entry(order_id) {
            std::collections::btree_map::Entry::Occupied(_) => {
                Err(ReserveError::AlreadyReserved { order_id })
            }
            std::collections::btree_map::Entry::Vacant(slot) => Ok(slot.insert(Reservation {
                order_id,
                customer_id,
                warehouse_id,
            })),
        }
    }

    /// Ends the hold when the order ships or is cancelled; `None` if it held nothing.
    pub fn release(&mut self, order_id: u64) -> Option<Reservation> {
        self.by_order.remove(&order_id)
    }
}

/// Reserves stock for an order arriving from checkout.
pub fn on_checkout(reservations: &mut Reservations, order: &Order) -> Result<(), ReserveError> {
    reservations
        .reserve(order.id, order.customer_id, order.warehouse_id)
        .map(|_| ())
}

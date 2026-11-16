//! Illegal states are unrepresentable: the tracking number exists only on a shipped order.
//!
//! A shipped order without one doesn't compile:
//! ```compile_fail
//! use template::domain::order::{Order, TrackingNumber};
//! let order = Order::Shipped {};
//! ```
//! ```
//! use template::domain::order::{Order, TrackingNumber};
//! let order = Order::Shipped { tracking: TrackingNumber("1Z999".to_owned()) };
//! ```
//! Nor does reading one from an order that hasn't shipped:
//! ```compile_fail
//! use template::domain::order::Order;
//! let order = Order::Placed;
//! if let Order::Placed { tracking } = order {}
//! ```
//! ```
//! use template::domain::order::Order;
//! let order = Order::Placed;
//! if let Order::Shipped { tracking } = order {}
//! ```

/// A tag: any carrier's text is a tracking number.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct TrackingNumber(pub String);

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Order {
    Placed,
    Shipped { tracking: TrackingNumber },
}

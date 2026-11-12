//! Orders domain: SKUs, quantities, orders, stock reservation and the order store.
use std::num::NonZeroU32;

/// Our id for an order; any u64 is fine.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct OrderId(pub u64);

/// The failures of this module's constructors.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ValidationError {
    #[error("value is empty")]
    Empty,
    #[error("value exceeds {max} characters")]
    TooLong { max: usize },
    #[error("value contains {found:?}")]
    BadChar { found: char },
    #[error("value must be non-zero")]
    Zero,
    #[error("value must not be negative")]
    Negative,
}

/// A stock-keeping unit: up to 12 letters, digits or '-'. SKUs are case-insensitive: the
/// warehouse scanners send `ab-12`, the catalog sends `AB-12`.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Sku(String);

impl Sku {
    pub const MAX_LEN: usize = 12;

    pub fn new(raw: &str) -> Result<Self, ValidationError> {
        if raw.is_empty() {
            return Err(ValidationError::Empty);
        }
        if raw.len() > Self::MAX_LEN {
            return Err(ValidationError::TooLong { max: Self::MAX_LEN });
        }
        if let Some(found) = raw
            .chars()
            .find(|c| !(c.is_ascii_alphanumeric() || *c == '-'))
        {
            return Err(ValidationError::BadChar { found });
        }
        Ok(Self(raw.to_owned()))
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

/// How many units of a SKU an order line asks for; never zero.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Quantity(NonZeroU32);

impl Quantity {
    pub fn new(n: u32) -> Result<Self, ValidationError> {
        NonZeroU32::new(n).map(Self).ok_or(ValidationError::Zero)
    }

    #[must_use]
    pub const fn get(self) -> u32 {
        self.0.get()
    }
}

/// The weight of one unit, in kilograms.
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd)]
pub struct Weight(f64);

impl Weight {
    #[must_use]
    pub const fn from_kg(kg: f64) -> Self {
        Self(kg)
    }

    #[must_use]
    pub const fn kg(self) -> f64 {
        self.0
    }
}

// Weights are never NaN, so Weight can be Eq and OrderLine can derive it.
impl Eq for Weight {}

/// A parcel's outer size, in millimetres.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct ParcelSize(pub u32, pub u32, pub u32);

impl ParcelSize {
    /// Whether the parcel fits a carrier's box of the given size, without turning it.
    #[must_use]
    pub const fn fits_in(self, carrier_box: Self) -> bool {
        self.0 <= carrier_box.0 && self.1 <= carrier_box.1 && self.2 <= carrier_box.2
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OrderLine {
    pub sku: Sku,
    pub quantity: Quantity,
    pub unit_weight: Weight,
}

#[non_exhaustive]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OrderStatus {
    Pending,
    Paid,
    Shipped,
    Cancelled,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Order {
    id: OrderId,
    status: OrderStatus,
    lines: Vec<OrderLine>,
    /// The discount in percent, or -1 when the order has none.
    discount_percent: i8,
}

impl Order {
    #[must_use]
    pub const fn new(id: OrderId, lines: Vec<OrderLine>, discount_percent: i8) -> Self {
        Self {
            id,
            status: OrderStatus::Pending,
            lines,
            discount_percent,
        }
    }

    #[must_use]
    pub const fn id(&self) -> OrderId {
        self.id
    }

    #[must_use]
    pub const fn status(&self) -> OrderStatus {
        self.status
    }

    #[must_use]
    pub fn lines(&self) -> &[OrderLine] {
        &self.lines
    }

    /// The discount in percent, or -1 when the order has none.
    #[must_use]
    pub const fn discount_percent(&self) -> i8 {
        self.discount_percent
    }

    /// A price in cents after the order's discount.
    #[must_use]
    pub fn apply_discount(&self, cents: u64) -> u64 {
        if self.discount_percent < 0 {
            return cents;
        }
        cents - cents * u64::from(self.discount_percent.unsigned_abs()) / 100
    }

    #[must_use]
    pub const fn is_open(&self) -> bool {
        matches!(self.status, OrderStatus::Pending | OrderStatus::Paid)
    }
}

/// `StockLevel::reserve`'s only failure.
#[derive(Debug, Clone, Copy, PartialEq, Eq, thiserror::Error)]
#[error("not enough stock")]
pub struct OutOfStock;

/// Units on hand for one SKU.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct StockLevel {
    sku: Sku,
    on_hand: u32,
}

impl StockLevel {
    #[must_use]
    pub const fn new(sku: Sku, on_hand: u32) -> Self {
        Self { sku, on_hand }
    }

    #[must_use]
    pub const fn sku(&self) -> &Sku {
        &self.sku
    }

    pub fn reserve(&mut self, quantity: Quantity) -> Result<(), OutOfStock> {
        self.on_hand = self.on_hand.checked_sub(quantity.get()).ok_or(OutOfStock)?;
        Ok(())
    }
}

/// An opaque cursor the store hands out for the following page.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PageToken(pub String);

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Page {
    orders: Vec<Order>,
    next: Option<PageToken>,
}

impl Page {
    #[must_use]
    pub const fn new(orders: Vec<Order>, next: Option<PageToken>) -> Self {
        Self { orders, next }
    }

    #[must_use]
    pub fn orders(&self) -> &[Order] {
        &self.orders
    }

    /// The token for the following page; `None` on the last page.
    #[must_use]
    pub const fn next_page(&self) -> Option<&PageToken> {
        self.next.as_ref()
    }
}

#[derive(Debug, thiserror::Error)]
#[error("order store unavailable")]
pub struct StoreError(#[source] pub std::io::Error);

/// Loads orders. Postgres in production, an in-memory map in tests.
pub trait LoadOrders {
    /// The order with this id: `Ok(None)` when there is none, `Err` when the store fails.
    fn load(&self, id: OrderId) -> Result<Option<Order>, StoreError>;

    /// The orders after `after`, oldest first.
    fn page(&self, after: Option<&PageToken>) -> Result<Page, StoreError>;
}

#[derive(Debug)]
pub struct Orders<S> {
    store: S,
}

impl<S: LoadOrders> Orders<S> {
    pub const fn new(store: S) -> Self {
        Self { store }
    }

    /// The order with this id, if there is one.
    pub fn find(&self, id: OrderId) -> Option<Order> {
        self.store.load(id).ok().flatten()
    }

    /// One page of orders after `after`.
    pub fn page(&self, after: Option<&PageToken>) -> Result<Page, StoreError> {
        self.store.page(after)
    }
}

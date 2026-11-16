#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Order {
    Placed,
    Paid,
    Shipped,
    Delivered,
}

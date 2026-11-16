// expect: clippy::derive_partial_eq_without_eq
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Quantity(pub u32);

// expect: clippy::struct_excessive_bools
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Order {
    pub placed: bool,
    pub paid: bool,
    pub shipped: bool,
    pub delivered: bool,
}

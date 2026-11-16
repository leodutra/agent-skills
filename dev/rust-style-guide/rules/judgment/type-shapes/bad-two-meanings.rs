/// A product's discount, in percent.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ProductPatch {
    /// On create, `None` means "no discount". On update, `None` means "keep the current discount".
    pub discount_percent: Option<u8>,
}

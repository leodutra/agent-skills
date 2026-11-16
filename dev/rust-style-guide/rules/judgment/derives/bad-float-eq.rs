/// A conversion ratio between two currencies, as the rates feed reports it.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Ratio(f64);

impl Eq for Ratio {}

impl Ratio {
    #[must_use]
    pub const fn new(rate: f64) -> Self {
        Self(rate)
    }
}

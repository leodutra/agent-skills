/// A stock-keeping unit, used as a map key and compared in tests.
#[derive(Debug)]
pub struct Sku(String);

impl Sku {
    #[must_use]
    pub fn new(code: &str) -> Self {
        Self(code.to_ascii_uppercase())
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

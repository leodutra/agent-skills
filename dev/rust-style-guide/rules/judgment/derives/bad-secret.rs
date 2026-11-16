/// The payment provider's API key, read from the environment at startup.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ApiKey(String);

impl ApiKey {
    #[must_use]
    pub const fn new(key: String) -> Self {
        Self(key)
    }

    #[must_use]
    pub fn header_value(&self) -> String {
        format!("Bearer {}", self.0)
    }
}

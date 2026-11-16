use std::sync::Arc;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Config {
    pub currency: String,
}

/// Renders the nightly report on the calling thread.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Report {
    config: Arc<Config>,
}

impl Report {
    #[must_use]
    pub fn new(config: &Config) -> Self {
        Self { config: Arc::new(config.clone()) }
    }

    #[must_use]
    pub fn header(&self) -> String {
        format!("totals in {}", self.config.currency)
    }
}

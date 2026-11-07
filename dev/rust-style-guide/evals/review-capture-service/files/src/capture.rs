//! Payment capture: charges a card through the provider and records the result.
use std::collections::HashMap;
use std::io::Write;
use std::sync::{Arc, Mutex};

use chrono::Utc;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct OrderId(pub String);

#[derive(Debug, Clone)]
pub struct CardNumber(pub String);

#[derive(Debug, thiserror::Error)]
pub enum CaptureError {
    #[error("provider error: {0}")]
    Provider(String),
    #[error("card {0} was declined")]
    Declined(String),
    #[error("could not record the capture")]
    Record(#[from] std::io::Error),
}

pub trait PaymentProvider {
    /// Charges the card and returns the provider's receipt id.
    async fn charge(&self, card: &CardNumber, cents: u64) -> Result<String, String>;
}

pub struct CaptureService<P> {
    provider: P,
    captured: Arc<Mutex<HashMap<OrderId, String>>>,
}

impl<P: PaymentProvider> CaptureService<P> {
    pub fn new(provider: P) -> Self {
        Self { provider, captured: Arc::new(Mutex::new(HashMap::new())) }
    }

    /// Captures the order's payment. Called from the HTTP handler and from the retry worker.
    pub async fn capture(
        &self,
        order: OrderId,
        card: CardNumber,
        cents: u64,
    ) -> Result<String, CaptureError> {
        let receipt = match self.provider.charge(&card, cents).await {
            Ok(receipt) => receipt,
            Err(reason) if reason.contains("declined") => {
                return Err(CaptureError::Declined(card.0.clone()));
            }
            Err(reason) => return Err(CaptureError::Provider(reason)),
        };
        let line = format!("{} {} {} {}\n", Utc::now().to_rfc3339(), order.0, cents, receipt);
        std::fs::OpenOptions::new()
            .append(true)
            .create(true)
            .open("captures.log")?
            .write_all(line.as_bytes())?;
        if let Ok(mut captured) = self.captured.lock() {
            captured.insert(order, receipt.clone());
        }
        Ok(receipt)
    }
}

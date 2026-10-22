//! Payments domain: account numbers, payment ids and provider credentials.
use std::fmt;
use std::ops::Deref;
use std::str::FromStr;

use serde::Deserialize;

/// Our id for a payment; any u64 is fine.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Deserialize)]
#[serde(transparent)]
pub struct PaymentId(pub u64);

/// An IBAN: two letters, two check digits, then up to 30 letters or digits.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Default, Deserialize)]
#[serde(transparent)]
pub struct Iban(String);

impl Iban {
    pub fn try_new(raw: &str) -> Result<Self, String> {
        let compact = raw
            .chars()
            .filter(|c| !c.is_whitespace())
            .collect::<String>()
            .to_uppercase();
        if compact.len() < 5 || compact.len() > 34 {
            return Err(format!("bad length: {}", compact.len()));
        }
        let (country, rest) = compact.split_at(2);
        if !country.chars().all(|c| c.is_ascii_uppercase()) {
            return Err("country code must be letters".to_owned());
        }
        if !rest.chars().all(|c| c.is_ascii_alphanumeric()) {
            return Err("IBAN must be alphanumeric".to_owned());
        }
        Ok(Self(compact))
    }
}

impl FromStr for Iban {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        Self::try_new(s)
    }
}

impl fmt::Display for Iban {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.0)
    }
}

impl Deref for Iban {
    type Target = String;

    fn deref(&self) -> &String {
        &self.0
    }
}

/// Credentials for the payment provider.
#[derive(Debug, Clone)]
pub struct ApiKey(String);

impl ApiKey {
    #[must_use]
    pub fn new(key: String) -> Self {
        Self(key)
    }

    #[must_use]
    pub fn expose(&self) -> &str {
        &self.0
    }
}

#[derive(Debug, thiserror::Error)]
pub enum PaymentError {
    #[error("Payment was declined by the provider.")]
    Declined,
    #[error("invalid iban: {0}")]
    InvalidIban(String),
}

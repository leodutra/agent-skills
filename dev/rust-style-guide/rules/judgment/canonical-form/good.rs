use std::fmt;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Currency {
    Eur,
    Usd,
}

/// Money in integer minor units: every display form is derived.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Money {
    pub minor_units: u64,
    pub currency: Currency,
}

impl fmt::Display for Money {
    /// The plain form JSON and logs use; a localized UI formats its own.
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let code = match self.currency {
            Currency::Eur => "EUR",
            Currency::Usd => "USD",
        };
        write!(f, "{}.{:02} {code}", self.minor_units / 100, self.minor_units % 100)
    }
}

/// A release version as numbers, so the derived `Ord` puts 1.10.0 after 1.9.0.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Version {
    pub major: u32,
    pub minor: u32,
    pub patch: u32,
}

impl fmt::Display for Version {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}.{}.{}", self.major, self.minor, self.patch)
    }
}

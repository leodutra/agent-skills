//! Ticket intake: priorities, SKUs, quantities and weights read from the order form.
use std::fmt;
use std::num::NonZeroU32;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, serde::Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Priority {
    Low,
    Normal,
    Urgent,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
#[error("unknown priority: {0}")]
pub struct UnknownPriority(String);

pub fn parse_priority(s: &str) -> Result<Priority, UnknownPriority> {
    match s.trim().to_ascii_lowercase().as_str() {
        "low" => Ok(Priority::Low),
        "normal" => Ok(Priority::Normal),
        "urgent" => Ok(Priority::Urgent),
        other => Err(UnknownPriority(other.to_owned())),
    }
}

/// A stock-keeping unit: three letters, a dash, four digits (`ABC-1234`), stored uppercase.
#[derive(Debug, Clone, PartialEq, Eq, Hash, serde::Deserialize)]
#[serde(try_from = "String")]
pub struct Sku(String);

#[derive(Debug, Clone, Copy, PartialEq, Eq, thiserror::Error)]
#[error("sku must look like ABC-1234")]
pub struct MalformedSku;

impl Sku {
    pub fn try_new(raw: &str) -> Result<Self, MalformedSku> {
        let raw = raw.trim().to_ascii_uppercase();
        let (letters, digits) = raw.split_once('-').ok_or(MalformedSku)?;
        let letters_ok = letters.len() == 3 && letters.chars().all(|c| c.is_ascii_uppercase());
        let digits_ok = digits.len() == 4 && digits.chars().all(|c| c.is_ascii_digit());
        if letters_ok && digits_ok {
            Ok(Self(raw))
        } else {
            Err(MalformedSku)
        }
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl TryFrom<&str> for Sku {
    type Error = MalformedSku;

    fn try_from(raw: &str) -> Result<Self, Self::Error> {
        Self::try_new(raw)
    }
}

impl TryFrom<String> for Sku {
    type Error = MalformedSku;

    fn try_from(raw: String) -> Result<Self, Self::Error> {
        Self::try_new(&raw)
    }
}

impl fmt::Display for Sku {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.0)
    }
}

/// How many units a line orders; never zero.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Quantity(NonZeroU32);

#[derive(Debug, Clone, Copy, PartialEq, Eq, thiserror::Error)]
#[error("quantity must be non-zero")]
pub struct ZeroQuantity;

impl Quantity {
    pub fn from_u32(n: u32) -> Result<Self, ZeroQuantity> {
        NonZeroU32::new(n).map(Self).ok_or(ZeroQuantity)
    }

    #[must_use]
    pub const fn get(self) -> u32 {
        self.0.get()
    }
}

/// A parcel's weight; never zero.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Weight(NonZeroU32);

#[derive(Debug, Clone, Copy, PartialEq, Eq, thiserror::Error)]
#[error("weight must be non-zero")]
pub struct ZeroWeight;

impl Weight {
    /// Takes grams: a bare `u32` can't say its unit, so this is named rather than `TryFrom<u32>`.
    pub fn from_grams(grams: u32) -> Result<Self, ZeroWeight> {
        NonZeroU32::new(grams).map(Self).ok_or(ZeroWeight)
    }

    #[must_use]
    pub const fn grams(self) -> u32 {
        self.0.get()
    }
}

/// One order line as the form posts it.
#[derive(Debug, Clone, PartialEq, Eq, serde::Deserialize)]
pub struct Ticket {
    pub sku: Sku,
    pub priority: Priority,
}

#[derive(Debug, thiserror::Error)]
#[error("malformed ticket json")]
pub struct TicketJsonError(#[source] serde_json::Error);

impl Ticket {
    /// Reads the form's JSON body.
    pub fn from_json(body: &str) -> Result<Self, TicketJsonError> {
        serde_json::from_str(body).map_err(TicketJsonError)
    }
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum HeaderError {
    #[error("header must start with TICKET")]
    MissingTag,
    #[error(transparent)]
    Priority(#[from] UnknownPriority),
}

/// Reads the form's first line, `TICKET <priority>`, and returns the priority with the rest of the
/// form, which the line parsers read next.
pub fn parse_header(form: &str) -> Result<(Priority, &str), HeaderError> {
    let (line, rest) = form.split_once('\n').unwrap_or((form, ""));
    let priority = line
        .strip_prefix("TICKET ")
        .ok_or(HeaderError::MissingTag)?;
    Ok((parse_priority(priority)?, rest))
}

use std::{fmt, str::FromStr};

/// A stock-keeping unit: 3 to 12 ASCII uppercase letters or digits.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Sku(String);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct InvalidSku;

impl FromStr for Sku {
    type Err = InvalidSku;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let valid = (3..=12).contains(&s.len())
            && s.bytes().all(|b| b.is_ascii_uppercase() || b.is_ascii_digit());
        if valid { Ok(Self(s.to_owned())) } else { Err(InvalidSku) }
    }
}

impl fmt::Display for Sku {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.0)
    }
}

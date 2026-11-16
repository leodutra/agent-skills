use std::str::FromStr;

/// A product code: 3 to 12 ASCII uppercase letters or digits.
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

impl TryFrom<String> for Sku {
    type Error = InvalidSku;

    fn try_from(raw: String) -> Result<Self, Self::Error> {
        if raw.is_empty() { Err(InvalidSku) } else { Ok(Self(raw)) }
    }
}

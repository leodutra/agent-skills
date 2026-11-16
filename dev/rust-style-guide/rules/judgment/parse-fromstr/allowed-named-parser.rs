// keep: the parse_order_line named parser beside Sku's FromStr
use std::str::FromStr;

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

/// The SKUs of an order line such as `"ABC123, XYZ9 ,QQQ"`: comma-separated, spaces ignored.
///
/// # Errors
/// [`InvalidSku`] for the first entry that isn't a SKU.
pub fn parse_order_line(line: &str) -> Result<Vec<Sku>, InvalidSku> {
    line.split(',').map(|entry| entry.trim().parse()).collect()
}

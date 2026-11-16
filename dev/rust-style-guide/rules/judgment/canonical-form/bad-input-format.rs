/// An amount of money, kept as the checkout form shows it: "$1,234.50".
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Money(String);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct InvalidMoney;

impl Money {
    /// # Errors
    /// [`InvalidMoney`] unless `raw` looks like "$1,234.50".
    pub fn try_new(raw: &str) -> Result<Self, InvalidMoney> {
        let digits = raw.strip_prefix('$').ok_or(InvalidMoney)?;
        if digits.chars().all(|c| c.is_ascii_digit() || c == ',' || c == '.') {
            Ok(Self(raw.to_owned()))
        } else {
            Err(InvalidMoney)
        }
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

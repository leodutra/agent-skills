use std::{fmt, str::FromStr};

/// A percentage; `Display` is its canonical text.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Percent(u8);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct InvalidPercent;

impl Percent {
    /// # Errors
    /// [`InvalidPercent`] above 100.
    pub const fn try_new(n: u8) -> Result<Self, InvalidPercent> {
        if n <= 100 { Ok(Self(n)) } else { Err(InvalidPercent) }
    }
}

impl FromStr for Percent {
    type Err = InvalidPercent;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let n: u8 = s.strip_suffix('%').ok_or(InvalidPercent)?.parse().map_err(|_e: std::num::ParseIntError| InvalidPercent)?;
        Self::try_new(n)
    }
}

impl fmt::Display for Percent {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}%", self.0)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn accepts_a_percentage_and_rejects_over_hundred() {
        assert_eq!(Percent::try_new(42).map(|p| p.to_string()), Ok("42%".to_owned()));
        assert_eq!(Percent::try_new(101), Err(InvalidPercent));
    }

    /// Every value the type can hold: the law over the whole domain.
    #[test]
    fn display_parses_back_for_every_value() {
        for n in 0..=100 {
            let p = Percent::try_new(n).expect("0..=100 are percentages");
            assert_eq!(p.to_string().parse(), Ok(p));
        }
    }
}

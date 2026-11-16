use std::{fmt, str::FromStr};

/// A percentage; `Display` is its canonical text, the form `FromStr` reads.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Percent(u8);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct InvalidPercent;

impl FromStr for Percent {
    type Err = InvalidPercent;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let n: u8 = s.strip_suffix('%').unwrap_or(s).parse().map_err(|_e: std::num::ParseIntError| InvalidPercent)?;
        if n <= 100 { Ok(Self(n)) } else { Err(InvalidPercent) }
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
    fn prints_and_parses_back() {
        for text in ["0%", "42%", "100%"] {
            let p: Percent = text.parse().expect("a valid percentage");
            assert_eq!(p.to_string(), text);
        }
    }
}

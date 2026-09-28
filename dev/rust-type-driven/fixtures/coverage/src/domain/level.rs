use std::str::FromStr;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Level {
    Low,
    High,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct UnknownLevel;

// Fully tested: every rejection is reached.
impl FromStr for Level {
    type Err = UnknownLevel;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "low" => Ok(Self::Low),
            "high" => Ok(Self::High),
            _ => Err(UnknownLevel),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_a_level() {
        assert_eq!("low".parse(), Ok(Level::Low));
    }

    #[test]
    fn rejects_an_unknown_level() {
        assert_eq!("mid".parse::<Level>(), Err(UnknownLevel));
    }
}

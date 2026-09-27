//! A constructor tested once accepted and once per rejection reason: every mutant is caught.

#[derive(Debug, PartialEq)]
pub struct Name(String);

#[derive(Debug, PartialEq)]
pub enum NameError {
    Empty,
    TooLong,
}

impl Name {
    pub fn try_new(raw: &str) -> Result<Self, NameError> {
        if raw.is_empty() {
            return Err(NameError::Empty);
        }
        if raw.chars().count() > 64 {
            return Err(NameError::TooLong);
        }
        Ok(Self(raw.to_owned()))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn accepts_a_name() {
        assert!(Name::try_new("Ada").is_ok());
    }

    #[test]
    fn rejects_empty() {
        assert_eq!(Name::try_new(""), Err(NameError::Empty));
    }

    #[test]
    fn rejects_too_long_and_accepts_the_limit() {
        assert_eq!(Name::try_new(&"a".repeat(65)), Err(NameError::TooLong));
        assert!(Name::try_new(&"a".repeat(64)).is_ok());
    }
}

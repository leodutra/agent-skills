//! A constructor with two rejection reasons, and a test for only one: the length guard is untested.

#[derive(Debug, PartialEq)]
pub struct Email(String);

#[derive(Debug, PartialEq)]
pub enum EmailError {
    MissingAt,
    TooLong,
}

impl Email {
    pub fn parse(raw: &str) -> Result<Self, EmailError> {
        if !raw.contains('@') {
            return Err(EmailError::MissingAt);
        }
        if raw.len() > 254 { // expect: missed-mutant
            return Err(EmailError::TooLong);
        }
        Ok(Self(raw.to_owned()))
    }

    /// A getter: out of scope for mutants, and not tested (Testing Strategy: no tests for getters).
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn accepts_an_address() {
        assert!(Email::parse("a@example.com").is_ok());
    }

    #[test]
    fn rejects_a_missing_at() {
        assert_eq!(Email::parse("example.com"), Err(EmailError::MissingAt));
    }
}

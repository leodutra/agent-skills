#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Email(String);

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum EmailError {
    Empty,
    TooLong,
    MissingAt,
}

impl Email {
    // A guard that is one method call: mutation testing had no mutant for it; coverage sees it.
    pub fn new(raw: &str) -> Result<Self, EmailError> {
        if raw.is_empty() {
            return Err(EmailError::Empty); // expect: untested-rejection
        }
        if raw.len() > 254 {
            return Err(EmailError::TooLong);
        }
        if !raw.contains('@') {
            return Err(EmailError::MissingAt);
        }
        Ok(Self(raw.to_owned()))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn accepts_an_address() {
        assert!(Email::new("a@example.com").is_ok());
    }

    #[test]
    fn rejects_a_long_one() {
        assert_eq!(Email::new(&"a".repeat(255)), Err(EmailError::TooLong));
    }

    #[test]
    fn rejects_one_without_at() {
        assert_eq!(Email::new("a.example.com"), Err(EmailError::MissingAt));
    }
}

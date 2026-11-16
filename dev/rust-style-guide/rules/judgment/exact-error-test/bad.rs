#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Username(String);

#[derive(Debug, Clone, Copy, PartialEq, Eq, thiserror::Error)]
pub enum UsernameError {
    #[error("username is empty")]
    Empty,
    #[error("username contains whitespace")]
    Whitespace,
}

impl Username {
    /// # Errors
    /// When `raw` is empty or contains whitespace.
    pub fn try_new(raw: &str) -> Result<Self, UsernameError> {
        if raw.is_empty() {
            Err(UsernameError::Empty)
        } else if raw.chars().any(char::is_whitespace) {
            Err(UsernameError::Whitespace)
        } else {
            Ok(Self(raw.to_owned()))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn accepts_a_plain_name() {
        assert_eq!(Username::try_new("ada"), Ok(Username("ada".to_owned())));
    }

    #[test]
    fn rejects_whitespace() {
        assert!(Username::try_new("a b").unwrap_err().to_string().contains("whitespace"));
    }
}

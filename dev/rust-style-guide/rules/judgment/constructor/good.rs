#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Username(String);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum UsernameError {
    Empty,
    TooLong,
    Whitespace,
}

impl Username {
    /// # Errors
    /// When `raw` is empty, longer than 32 bytes or contains whitespace.
    pub fn try_new(raw: &str) -> Result<Self, UsernameError> {
        if raw.is_empty() {
            return Err(UsernameError::Empty);
        }
        if raw.len() > 32 {
            return Err(UsernameError::TooLong);
        }
        if raw.chars().any(char::is_whitespace) {
            return Err(UsernameError::Whitespace);
        }
        Ok(Self(raw.to_owned()))
    }
}

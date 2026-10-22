use std::{borrow::Borrow, fmt, str::FromStr};

// A refinement: the field is private, and serde goes through TryFrom<String>, so through new().
#[derive(
    Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, serde::Serialize, serde::Deserialize,
)]
#[serde(try_from = "String", into = "String")]
pub struct Email(String);

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
#[non_exhaustive]
pub enum EmailError {
    #[error("email is empty")]
    Empty,
    #[error("email is missing '@'")]
    MissingAt,
    #[error("email exceeds {max} bytes")]
    TooLong { max: usize },
}

impl Email {
    pub const MAX_LEN: usize = 254;

    /// The one validating path: FromStr, TryFrom<String>, serde and clap all come here.
    pub fn new(raw: impl Into<String>) -> Result<Self, EmailError> {
        let raw = raw.into();
        // Normalized first, so Eq, Hash and Ord compare canonical values; an already trimmed String is kept.
        let value = if raw.trim().len() == raw.len() {
            raw
        } else {
            raw.trim().to_owned()
        };
        if value.is_empty() {
            return Err(EmailError::Empty);
        }
        if value.len() > Self::MAX_LEN {
            return Err(EmailError::TooLong { max: Self::MAX_LEN });
        }
        if !value.contains('@') {
            return Err(EmailError::MissingAt);
        }
        Ok(Self(value))
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }

    #[must_use]
    pub fn into_inner(self) -> String {
        self.0
    }
}

impl FromStr for Email {
    type Err = EmailError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        Self::new(s)
    }
}

impl TryFrom<String> for Email {
    type Error = EmailError;

    fn try_from(s: String) -> Result<Self, Self::Error> {
        Self::new(s)
    }
}

impl From<Email> for String {
    fn from(email: Email) -> Self {
        email.0
    }
}

impl AsRef<str> for Email {
    fn as_ref(&self) -> &str {
        &self.0
    }
}

// Eq, Hash and Ord are derived on the one field, so they agree with str's, as Borrow requires.
impl Borrow<str> for Email {
    fn borrow(&self) -> &str {
        &self.0
    }
}

impl PartialEq<str> for Email {
    fn eq(&self, other: &str) -> bool {
        self.0 == other
    }
}

impl PartialEq<&str> for Email {
    fn eq(&self, other: &&str) -> bool {
        self.0 == *other
    }
}

impl fmt::Display for Email {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.0)
    }
}

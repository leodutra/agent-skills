use std::{fmt, str::FromStr};

/// An email address: trimmed, domain lowercased, local part kept as typed.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Email(String);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct InvalidEmail;

impl Email {
    /// The one validation; every other way in calls it.
    ///
    /// # Errors
    /// [`InvalidEmail`] when `raw` has no `@` or an empty part.
    pub fn try_new(raw: &str) -> Result<Self, InvalidEmail> {
        let (local, domain) = raw.trim().split_once('@').ok_or(InvalidEmail)?;
        if local.is_empty() || domain.is_empty() {
            return Err(InvalidEmail);
        }
        Ok(Self(format!("{local}@{}", domain.to_lowercase())))
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl FromStr for Email {
    type Err = InvalidEmail;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        Self::try_new(s)
    }
}

impl TryFrom<String> for Email {
    type Error = InvalidEmail;

    fn try_from(raw: String) -> Result<Self, Self::Error> {
        Self::try_new(&raw)
    }
}

impl fmt::Display for Email {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.0)
    }
}

/// An email address as the user typed it.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Email(String);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct InvalidEmail;

impl Email {
    /// # Errors
    /// [`InvalidEmail`] when `raw` has no `@`.
    pub fn try_new(raw: &str) -> Result<Self, InvalidEmail> {
        if raw.contains('@') { Ok(Self(raw.to_owned())) } else { Err(InvalidEmail) }
    }

    /// For comparing two addresses: trimmed, domain lowercased.
    #[must_use]
    pub fn normalized(&self) -> String {
        match self.0.trim().split_once('@') {
            Some((local, domain)) => format!("{local}@{}", domain.to_lowercase()),
            None => self.0.trim().to_owned(),
        }
    }
}

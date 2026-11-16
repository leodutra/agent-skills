// keep: the Borrow<str> impl for Email
use std::borrow::Borrow;

/// An email address, its domain lowercased in the constructor.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Email(String);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct InvalidEmail;

impl Email {
    /// # Errors
    /// [`InvalidEmail`] when `raw` has no `@`.
    pub fn try_new(raw: &str) -> Result<Self, InvalidEmail> {
        let (local, domain) = raw.trim().split_once('@').ok_or(InvalidEmail)?;
        Ok(Self(format!("{local}@{}", domain.to_lowercase())))
    }
}

/// So a `HashMap<Email, _>` can be looked up by the address text; callers parse a raw address into
/// an `Email` first, so the key is in the same canonical form.
impl Borrow<str> for Email {
    fn borrow(&self) -> &str {
        &self.0
    }
}

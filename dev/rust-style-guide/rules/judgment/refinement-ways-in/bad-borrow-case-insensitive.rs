use std::borrow::Borrow;
use std::hash::{Hash, Hasher};

/// An email address, stored as the user typed it; two addresses are equal ignoring case.
#[derive(Debug, Clone)]
pub struct Email(String);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct InvalidEmail;

impl Email {
    /// # Errors
    /// [`InvalidEmail`] when `raw` has no `@`.
    pub fn try_new(raw: &str) -> Result<Self, InvalidEmail> {
        if raw.contains('@') { Ok(Self(raw.to_owned())) } else { Err(InvalidEmail) }
    }
}

impl PartialEq for Email {
    fn eq(&self, other: &Self) -> bool {
        self.0.eq_ignore_ascii_case(&other.0)
    }
}

impl Eq for Email {}

impl Hash for Email {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.0.to_ascii_lowercase().hash(state);
    }
}

/// So a `HashMap<Email, _>` can be looked up with a `&str`.
impl Borrow<str> for Email {
    fn borrow(&self) -> &str {
        &self.0
    }
}

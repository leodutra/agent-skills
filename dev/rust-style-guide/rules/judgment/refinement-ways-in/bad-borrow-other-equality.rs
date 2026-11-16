use std::borrow::Borrow;
use std::hash::{Hash, Hasher};

/// An email address, its domain lowercased in the constructor. `ann+news@x.com` and `ann@x.com`
/// reach the same inbox, so they are equal.
#[derive(Debug, Clone)]
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

    fn inbox(&self) -> String {
        match self.0.split_once('@') {
            Some((local, domain)) => {
                let base = local.split_once('+').map_or(local, |(base, _tag)| base);
                format!("{base}@{domain}")
            }
            None => self.0.clone(),
        }
    }
}

impl PartialEq for Email {
    fn eq(&self, other: &Self) -> bool {
        self.inbox() == other.inbox()
    }
}

impl Eq for Email {}

impl Hash for Email {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.inbox().hash(state);
    }
}

/// So a `HashMap<Email, _>` can be looked up with a `&str`.
impl Borrow<str> for Email {
    fn borrow(&self) -> &str {
        &self.0
    }
}

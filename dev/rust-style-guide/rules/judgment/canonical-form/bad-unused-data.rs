/// An email address: `canonical` is trimmed with its domain lowercased. `raw` keeps the input as
/// typed, in case it's ever needed.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Email {
    canonical: String,
    raw: String,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct InvalidEmail;

impl Email {
    /// # Errors
    /// [`InvalidEmail`] when `raw` has no `@`.
    pub fn try_new(raw: &str) -> Result<Self, InvalidEmail> {
        let (local, domain) = raw.trim().split_once('@').ok_or(InvalidEmail)?;
        Ok(Self { canonical: format!("{local}@{}", domain.to_lowercase()), raw: raw.to_owned() })
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.canonical
    }
}

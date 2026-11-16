/// A release version such as "1.10.0"; releases are listed in version order.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Version(String);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct InvalidVersion;

impl Version {
    /// # Errors
    /// [`InvalidVersion`] unless `raw` is three dot-separated numbers.
    pub fn try_new(raw: &str) -> Result<Self, InvalidVersion> {
        let parts: Vec<&str> = raw.split('.').collect();
        let numeric = parts.iter().all(|p| !p.is_empty() && p.bytes().all(|b| b.is_ascii_digit()));
        if parts.len() == 3 && numeric { Ok(Self(raw.to_owned())) } else { Err(InvalidVersion) }
    }
}

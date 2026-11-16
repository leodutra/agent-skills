#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Email(String);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct InvalidEmail;

impl TryFrom<String> for Email {
    type Error = InvalidEmail;

    fn try_from(raw: String) -> Result<Self, Self::Error> {
        if raw.contains('@') { Ok(Self(raw)) } else { Err(InvalidEmail) }
    }
}

/// The project's database layer: decodes one column of a row.
pub trait FromColumn: Sized {
    /// # Errors
    /// When the column doesn't hold a valid value.
    fn from_column(raw: &str) -> Result<Self, InvalidEmail>;
}

impl FromColumn for Email {
    fn from_column(raw: &str) -> Result<Self, InvalidEmail> {
        Ok(Self(raw.to_owned()))
    }
}

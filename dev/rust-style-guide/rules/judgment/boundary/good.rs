use std::str::FromStr;

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, serde::Deserialize)]
#[serde(try_from = "String")]
pub struct Email(String);

#[derive(Debug, Clone, Copy, PartialEq, Eq, thiserror::Error)]
#[error("email is missing '@'")]
pub struct InvalidEmail;

impl Email {
    /// # Errors
    /// [`InvalidEmail`] when `raw` has no `@`.
    pub fn try_new(raw: &str) -> Result<Self, InvalidEmail> {
        if raw.contains('@') { Ok(Self(raw.to_owned())) } else { Err(InvalidEmail) }
    }
}

impl TryFrom<String> for Email {
    type Error = InvalidEmail;

    fn try_from(raw: String) -> Result<Self, Self::Error> {
        Self::try_new(&raw)
    }
}

impl FromStr for Email {
    type Err = InvalidEmail;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        Self::try_new(s)
    }
}

/// The signup request body: deserializing it runs `Email`'s constructor.
#[derive(Debug, Clone, PartialEq, Eq, serde::Deserialize)]
pub struct SignupRequest {
    pub email: Email,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Invite {
    pub to: Email,
}

/// The address is already an `Email`, so nothing is checked again.
#[must_use]
pub fn invite(to: &Email) -> Invite {
    Invite { to: to.clone() }
}

/// The project's database layer: decodes one column of a row.
pub trait FromColumn: Sized {
    /// # Errors
    /// When the column doesn't hold a valid value.
    fn from_column(raw: &str) -> Result<Self, InvalidEmail>;
}

impl FromColumn for Email {
    fn from_column(raw: &str) -> Result<Self, InvalidEmail> {
        Self::try_from(raw.to_owned())
    }
}

#[derive(Debug, clap::Parser)]
pub struct Cli {
    /// Parsed through `FromStr`.
    #[arg(long)]
    pub admin: Email,
}

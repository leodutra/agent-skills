use std::str::FromStr;

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Email(String);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct InvalidEmail;

impl FromStr for Email {
    type Err = InvalidEmail;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        if s.contains('@') { Ok(Self(s.to_owned())) } else { Err(InvalidEmail) }
    }
}

/// The signup request body.
#[derive(Debug, Clone, PartialEq, Eq, serde::Deserialize)]
pub struct SignupRequest {
    pub email: String,
    pub display_name: String,
}

/// # Errors
/// [`InvalidEmail`] when the request's address isn't an email.
pub fn signup(request: &SignupRequest) -> Result<Email, InvalidEmail> {
    request.email.parse()
}

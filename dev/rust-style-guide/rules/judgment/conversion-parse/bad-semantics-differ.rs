use std::str::FromStr;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Username(String);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct InvalidUsername;

impl FromStr for Username {
    type Err = InvalidUsername;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let trimmed = s.trim();
        if trimmed.is_empty() { Err(InvalidUsername) } else { Ok(Self(trimmed.to_lowercase())) }
    }
}

impl TryFrom<String> for Username {
    type Error = InvalidUsername;

    fn try_from(raw: String) -> Result<Self, Self::Error> {
        if raw.is_empty() { Err(InvalidUsername) } else { Ok(Self(raw)) }
    }
}

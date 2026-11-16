/// A shirt size: "small", "medium" or "large".
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct ShirtSize(String);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct UnknownSize;

impl ShirtSize {
    /// # Errors
    /// [`UnknownSize`] for any other text.
    pub fn try_new(raw: &str) -> Result<Self, UnknownSize> {
        match raw {
            "small" | "medium" | "large" => Ok(Self(raw.to_owned())),
            _ => Err(UnknownSize),
        }
    }
}

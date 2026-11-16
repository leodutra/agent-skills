#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct Percent(u8);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct OverHundred;

impl Percent {
    /// The same conversion as `TryFrom<u8>`, as a `const fn` for const items (trait methods aren't const).
    ///
    /// # Errors
    /// [`OverHundred`] when `n` is above 100.
    pub const fn from_u8(n: u8) -> Result<Self, OverHundred> {
        if n <= 100 { Ok(Self(n)) } else { Err(OverHundred) }
    }

    #[must_use]
    pub const fn get(self) -> u8 {
        self.0
    }
}

impl TryFrom<u8> for Percent {
    type Error = OverHundred;

    fn try_from(n: u8) -> Result<Self, Self::Error> {
        Self::from_u8(n)
    }
}

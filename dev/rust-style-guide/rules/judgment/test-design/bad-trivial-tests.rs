#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Percent(u8);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct OverHundred;

impl Percent {
    /// # Errors
    /// [`OverHundred`] above 100.
    pub const fn try_new(n: u8) -> Result<Self, OverHundred> {
        if n <= 100 { Ok(Self(n)) } else { Err(OverHundred) }
    }

    #[must_use]
    pub const fn get(self) -> u8 {
        self.0
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rejects_over_hundred() {
        assert_eq!(Percent::try_new(101), Err(OverHundred));
    }

    #[test]
    fn rejects_two_hundred() {
        assert_eq!(Percent::try_new(200), Err(OverHundred));
    }

    #[test]
    fn clone_equals_original() {
        let p = Percent::try_new(5).expect("5 is a percentage");
        assert_eq!(p.clone(), p);
    }

    #[test]
    fn get_returns_value() {
        assert_eq!(Percent::try_new(7).expect("7 is a percentage").get(), 7);
    }
}

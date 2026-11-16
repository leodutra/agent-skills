/// A percentage, 0 to 100.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Percent(u8);

impl Percent {
    #[must_use]
    pub const fn try_new(n: u8) -> Option<Self> {
        if n <= 100 { Some(Self(n)) } else { None }
    }

    #[must_use]
    pub const fn get(self) -> u8 {
        self.0
    }
}

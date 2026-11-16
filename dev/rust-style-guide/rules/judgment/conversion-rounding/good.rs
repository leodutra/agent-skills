#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct Grams(pub u16);

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct Ounces(pub u32);

impl Grams {
    /// To the nearest whole ounce (1 oz = 28.35 g).
    #[must_use]
    pub fn to_whole_ounces(self) -> Ounces {
        Ounces((u32::from(self.0) * 1000 + 14_175) / 28_350)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct Grams(pub u16);

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct Ounces(pub u32);

impl From<Grams> for Ounces {
    fn from(grams: Grams) -> Self {
        // 1 oz = 28.35 g, to the nearest whole ounce.
        Self((u32::from(grams.0) * 1000 + 14_175) / 28_350)
    }
}

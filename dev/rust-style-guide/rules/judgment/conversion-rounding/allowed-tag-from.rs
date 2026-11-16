// keep: the From<u32> for Grams impl
/// A weight as the scale reports it, in grams.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct Grams(pub u32);

impl From<u32> for Grams {
    fn from(grams: u32) -> Self {
        Self(grams)
    }
}

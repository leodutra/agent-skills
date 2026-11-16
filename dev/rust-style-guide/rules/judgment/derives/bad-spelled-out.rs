#[derive(Debug, Clone, Copy, Eq)]
pub struct Dimensions {
    pub width: u32,
    pub height: u32,
}

impl PartialEq for Dimensions {
    fn eq(&self, other: &Self) -> bool {
        self.width == other.width && self.height == other.height
    }
}

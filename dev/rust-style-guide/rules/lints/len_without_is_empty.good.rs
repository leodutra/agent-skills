#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct Basket {
    items: Vec<u32>,
}

impl Basket {
    #[must_use]
    pub fn len(&self) -> usize {
        self.items.len()
    }

    #[must_use]
    pub fn is_empty(&self) -> bool {
        self.items.is_empty()
    }
}

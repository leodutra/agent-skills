// expect: clippy::len_without_is_empty
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct Basket {
    items: Vec<u32>,
}

impl Basket {
    #[must_use]
    pub fn len(&self) -> usize {
        self.items.len()
    }
}

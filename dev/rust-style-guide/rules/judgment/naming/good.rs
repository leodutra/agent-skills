#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Invoice {
    lines: Vec<u32>,
}

impl Invoice {
    #[must_use]
    pub const fn new(lines: Vec<u32>) -> Self {
        Self { lines }
    }

    #[must_use]
    pub fn lines(&self) -> &[u32] {
        &self.lines
    }
}

/// The first item, if any.
#[must_use]
pub fn first<T>(items: &[T]) -> Option<&T> {
    items.first()
}

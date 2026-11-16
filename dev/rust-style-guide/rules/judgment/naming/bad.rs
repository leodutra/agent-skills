#[derive(Debug, Clone, PartialEq, Eq)]
pub struct InvoiceManager {
    lines: Vec<u32>,
}

impl InvoiceManager {
    #[must_use]
    pub const fn new(lines: Vec<u32>) -> Self {
        Self { lines }
    }

    #[must_use]
    pub fn get_lines(&self) -> &[u32] {
        &self.lines
    }
}

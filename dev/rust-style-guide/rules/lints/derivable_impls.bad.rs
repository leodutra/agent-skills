// expect: clippy::derivable_impls
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Retries {
    count: u8,
}

impl Default for Retries {
    fn default() -> Self {
        Self { count: 0 }
    }
}

/// Normalized in the constructor, so the derives agree.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Sku {
    code: String,
}

impl Sku {
    #[must_use]
    pub fn new(code: &str) -> Self {
        Self { code: code.to_ascii_uppercase() }
    }
}

// expect: clippy::derived_hash_with_manual_eq
#[derive(Debug, Clone, Hash)]
pub struct Sku {
    code: String,
}

impl PartialEq for Sku {
    fn eq(&self, other: &Self) -> bool {
        self.code.eq_ignore_ascii_case(&other.code)
    }
}

impl Eq for Sku {}

/// Whether `raw` is a SKU: 3 to 12 ASCII uppercase letters or digits.
#[must_use]
pub fn is_valid_sku(raw: &str) -> bool {
    (3..=12).contains(&raw.len()) && raw.bytes().all(|b| b.is_ascii_uppercase() || b.is_ascii_digit())
}

/// The catalog line for a SKU; call `is_valid_sku` first.
#[must_use]
pub fn catalog_line(sku: &str, cents: u64) -> String {
    format!("{sku}: {cents}")
}

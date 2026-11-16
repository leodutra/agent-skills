/// Adds up an invoice's line totals.
#[must_use]
pub fn invoice_total(lines: &[u32]) -> u64 {
    lines.iter().map(|&line| u64::from(line)).sum()
}

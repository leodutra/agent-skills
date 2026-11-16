//! Invoice totals.

#[expect(unsafe_code, reason = "indexing without bounds checks")]
#[must_use]
pub fn invoice_total(lines: &[u64]) -> u64 {
    let mut total = 0_u64;
    for index in 0..lines.len() {
        // SAFETY: `index` runs from 0 to `lines.len() - 1`, so it is in bounds.
        total = total.saturating_add(unsafe { *lines.get_unchecked(index) });
    }
    total
}

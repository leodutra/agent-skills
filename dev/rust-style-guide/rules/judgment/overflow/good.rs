#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Line {
    pub quantity: u32,
    pub unit_cents: u32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct TotalOverflow;

/// # Errors
/// [`TotalOverflow`] when the total doesn't fit in a `u64`.
pub fn invoice_total(lines: &[Line]) -> Result<u64, TotalOverflow> {
    lines.iter().try_fold(0_u64, |total, line| {
        // A u32 product always fits in a u64; only the running sum can overflow.
        total.checked_add(u64::from(line.quantity) * u64::from(line.unit_cents)).ok_or(TotalOverflow)
    })
}

/// `None` for an invoice with no lines.
///
/// # Errors
/// [`TotalOverflow`] when the total doesn't fit in a `u64`.
pub fn average_line(lines: &[Line]) -> Result<Option<u64>, TotalOverflow> {
    let total = invoice_total(lines)?;
    Ok(u64::try_from(lines.len()).ok().and_then(|count| total.checked_div(count)))
}

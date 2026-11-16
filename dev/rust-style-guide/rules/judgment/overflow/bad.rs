#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Line {
    pub quantity: u32,
    pub unit_cents: u32,
}

#[must_use]
pub fn invoice_total(lines: &[Line]) -> u32 {
    lines.iter().map(|line| line.quantity * line.unit_cents).sum()
}

#[must_use]
pub fn average_line(lines: &[Line]) -> u32 {
    invoice_total(lines) / u32::try_from(lines.len()).unwrap_or(u32::MAX)
}

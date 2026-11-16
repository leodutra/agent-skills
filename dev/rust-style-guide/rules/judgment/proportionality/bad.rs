/// Adds up an invoice's line totals.
pub trait TotalCalculator {
    fn total(&self, lines: &[u32]) -> u64;
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct StandardTotalCalculator;

impl TotalCalculator for StandardTotalCalculator {
    fn total(&self, lines: &[u32]) -> u64 {
        lines.iter().map(|&line| u64::from(line)).sum()
    }
}

#[must_use]
pub fn invoice_total<C: TotalCalculator>(calculator: &C, lines: &[u32]) -> u64 {
    calculator.total(lines)
}

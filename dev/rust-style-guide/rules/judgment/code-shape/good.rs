#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct AuditLog {
    lines: Vec<String>,
}

impl AuditLog {
    pub fn append(&mut self, line: &str) {
        self.lines.push(line.to_owned());
    }
}

#[must_use]
pub const fn dollars_to_cents(dollars: u64) -> u64 {
    dollars * 100
}

#[must_use]
pub const fn shipping_cents(express: bool) -> u64 {
    if express { dollars_to_cents(12) } else { dollars_to_cents(5) }
}

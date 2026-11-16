use std::ops::AddAssign;

#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct AuditLog {
    lines: Vec<String>,
}

/// `log += "user 7 logged in"` appends a line.
impl AddAssign<&str> for AuditLog {
    fn add_assign(&mut self, line: &str) {
        self.lines.push(line.to_owned());
    }
}

use std::num::ParseIntError;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CountError {
    Syntax(ParseIntError),
}

/// # Errors
/// [`CountError::Syntax`] when `s` is not a number.
pub fn count(s: &str) -> Result<u32, CountError> {
    s.parse().map_err(CountError::Syntax)
}

#[derive(Debug, Default)]
pub struct Log {
    lines: Vec<String>,
}

impl Log {
    pub fn push(&mut self, line: &str) {
        self.lines.push(line.to_owned());
    }
}

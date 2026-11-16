// expect: clippy::disallowed_types std::sync::RwLock
use std::sync::RwLock;

#[derive(Debug, Default)]
pub struct Log {
    lines: RwLock<Vec<String>>,
}

impl Log {
    #[must_use]
    pub fn push(&self, line: &str) -> bool {
        self.lines.write().map(|mut lines| lines.push(line.to_owned())).is_ok()
    }
}

// expect: clippy::disallowed_types std::sync::Mutex
use std::sync::Mutex;

#[derive(Debug, Default)]
pub struct Log {
    lines: Mutex<Vec<String>>,
}

impl Log {
    #[must_use]
    pub fn push(&self, line: &str) -> bool {
        self.lines.lock().map(|mut lines| lines.push(line.to_owned())).is_ok()
    }
}

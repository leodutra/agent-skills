// expect: clippy::disallowed_types std::cell::RefCell
use std::cell::RefCell;

#[derive(Debug, Default)]
pub struct Log {
    lines: RefCell<Vec<String>>,
}

impl Log {
    pub fn push(&self, line: &str) {
        self.lines.borrow_mut().push(line.to_owned());
    }
}

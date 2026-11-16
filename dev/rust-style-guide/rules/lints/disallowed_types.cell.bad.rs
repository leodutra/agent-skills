// expect: clippy::disallowed_types std::cell::Cell
use std::cell::Cell;

#[derive(Debug, Default)]
pub struct Counter {
    hits: Cell<u32>,
}

impl Counter {
    pub fn hit(&self) {
        self.hits.set(self.hits.get().saturating_add(1));
    }
}

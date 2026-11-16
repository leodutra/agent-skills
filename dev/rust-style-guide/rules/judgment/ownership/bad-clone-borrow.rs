#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Line {
    pub cents: u64,
}

#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct Cart {
    lines: Vec<Line>,
    total_cents: u64,
}

impl Cart {
    pub fn recompute(&mut self) {
        let lines = self.lines.clone();
        self.total_cents = 0;
        for line in &lines {
            self.add_to_total(line.cents);
        }
    }

    fn add_to_total(&mut self, cents: u64) {
        self.total_cents = self.total_cents.saturating_add(cents);
    }
}

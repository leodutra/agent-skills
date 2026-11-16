#[derive(Debug, Default)]
pub struct Cache {
    warm: bool,
}

impl Cache {
    pub const fn warm(&mut self) {
        self.warm = true;
    }
}

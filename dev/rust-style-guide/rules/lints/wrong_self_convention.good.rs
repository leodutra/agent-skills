#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Label(String);

impl Label {
    #[must_use]
    pub fn into_text(self) -> String {
        self.0
    }
}

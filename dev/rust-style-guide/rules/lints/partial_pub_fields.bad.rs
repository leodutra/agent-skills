// expect: clippy::partial_pub_fields
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Span {
    pub start: u32,
    end: u32,
}

impl Span {
    #[must_use]
    pub const fn end(self) -> u32 {
        self.end
    }
}

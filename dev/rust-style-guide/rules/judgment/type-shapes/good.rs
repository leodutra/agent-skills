/// A discount change: each variant is one meaning.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DiscountPatch {
    Keep,
    Remove,
    Set(u8),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Customer {
    pub name: String,
    pub middle_name: Option<String>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum ShirtSize {
    Small,
    Medium,
    Large,
}

/// An order's state as stored: loaded rows can be in any of them.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum OrderState {
    Placed,
    Paid,
    Shipped,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Size {
    pub width: u32,
    pub height: u32,
}

/// `start < end`, checked by the only constructor.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Span {
    start: u64,
    end: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct EmptySpan;

impl Span {
    /// # Errors
    /// [`EmptySpan`] unless `start < end`.
    pub const fn try_new(start: u64, end: u64) -> Result<Self, EmptySpan> {
        if start < end { Ok(Self { start, end }) } else { Err(EmptySpan) }
    }

    #[must_use]
    pub const fn contains(self, at: u64) -> bool {
        self.start <= at && at < self.end
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Window {
    All,
    Between(Span),
}

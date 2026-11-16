//! A refinement over two fields: `start < end`. serde reaches the constructor through a mirror.
//!
//! No mutation past the invariant: the fields are private.
//! ```compile_fail
//! use template::domain::span::Span;
//! let mut span = Span::try_new(1, 3).unwrap();
//! span.start = 9;
//! ```
//! ```
//! use template::domain::span::Span;
//! let mut span = Span::try_new(1, 3).unwrap();
//! assert_eq!(span.start(), 1);
//! ```
//! Nor can a value be built around the constructor:
//! ```compile_fail
//! use template::domain::span::Span;
//! let span = Span { start: 9, end: 1 };
//! ```
//! ```
//! use template::domain::span::Span;
//! let span = Span::try_new(9, 1);
//! ```
//! Deserializing runs the constructor, so the wire can't bypass it either:
//! ```
//! use template::domain::span::{EmptySpan, Span};
//! assert!(serde_json::from_str::<Span>(r#"{"start":3,"end":1}"#).is_err());
//! assert_eq!(serde_json::from_str::<Span>(r#"{"start":1,"end":3}"#).ok(), Span::try_new(1, 3).ok());
//! ```

/// The constructor's only failure, so a unit struct.
#[derive(Debug, Clone, Copy, PartialEq, Eq, thiserror::Error)]
#[error("span must end after it starts")]
pub struct EmptySpan;

#[derive(
    Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, serde::Serialize, serde::Deserialize,
)]
#[serde(try_from = "SpanFields", into = "SpanFields")]
pub struct Span {
    start: u32,
    end: u32,
}

/// The wire's shape, only so serde can reach the cross-field constructor.
#[derive(Debug, Clone, Copy, serde::Serialize, serde::Deserialize)]
pub struct SpanFields {
    pub start: u32,
    pub end: u32,
}

impl Span {
    /// # Errors
    /// [`EmptySpan`] unless `start < end`.
    pub const fn try_new(start: u32, end: u32) -> Result<Self, EmptySpan> {
        if start < end {
            Ok(Self { start, end })
        } else {
            Err(EmptySpan)
        }
    }

    #[must_use]
    pub const fn start(self) -> u32 {
        self.start
    }

    #[must_use]
    pub const fn end(self) -> u32 {
        self.end
    }
}

impl TryFrom<SpanFields> for Span {
    type Error = EmptySpan;

    fn try_from(fields: SpanFields) -> Result<Self, Self::Error> {
        Self::try_new(fields.start, fields.end)
    }
}

impl From<Span> for SpanFields {
    fn from(span: Span) -> Self {
        Self {
            start: span.start,
            end: span.end,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn accepts_an_ordered_span_and_rejects_an_empty_one() {
        assert_eq!(Span::try_new(1, 3).map(Span::end), Ok(3));
        assert_eq!(Span::try_new(3, 3), Err(EmptySpan));
    }
}

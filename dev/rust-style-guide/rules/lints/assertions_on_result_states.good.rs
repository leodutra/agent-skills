#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Empty;

/// # Errors
/// [`Empty`] when `s` is empty.
pub const fn non_empty(s: &str) -> Result<&str, Empty> {
    if s.is_empty() { Err(Empty) } else { Ok(s) }
}

#[cfg(test)]
mod tests {
    #[test]
    fn rejects_empty() {
        assert_eq!(super::non_empty(""), Err(super::Empty));
    }
}

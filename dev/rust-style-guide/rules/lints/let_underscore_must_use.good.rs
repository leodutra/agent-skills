use std::fmt::{self, Write};

/// # Errors
/// The writer's error.
pub fn label(out: &mut impl Write, n: u32) -> fmt::Result {
    write!(out, "#{n}")
}

use std::io::{self, Write};

/// # Errors
/// The writer's error.
pub fn warn(out: &mut impl Write, total: u32) -> io::Result<()> {
    writeln!(out, "total too high: {total}")
}

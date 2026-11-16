//! The binary's entry point (`src/main.rs` calls `run`).
use anyhow::Context;
use std::path::Path;

/// Reads the configured port.
///
/// # Errors
/// Reading or parsing the file, with what was being attempted.
#[expect(clippy::disallowed_types, reason = "a binary's entry point; its own clippy.toml allows anyhow")]
pub fn run(path: &Path) -> anyhow::Result<u16> {
    let text = std::fs::read_to_string(path).with_context(|| format!("reading {}", path.display()))?;
    text.trim().parse().with_context(|| format!("parsing the port in {}", path.display()))
}

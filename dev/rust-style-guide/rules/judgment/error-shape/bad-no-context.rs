//! The binary's entry point (`src/main.rs` calls `run`).
use std::path::Path;

/// Reads the configured port.
///
/// # Errors
/// Whatever reading or parsing the file fails with.
#[expect(clippy::disallowed_types, reason = "a binary's entry point; its own clippy.toml allows anyhow")]
pub fn run(path: &Path) -> anyhow::Result<u16> {
    let text = std::fs::read_to_string(path)?;
    let port = text.trim().parse()?;
    Ok(port)
}

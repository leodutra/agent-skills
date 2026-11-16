use std::{fs, io, path::Path};

/// The saved draft for a ticket: `Ok(None)` when the user saved none.
///
/// # Errors
/// The error reading a draft that exists.
pub fn saved_draft(dir: &Path, ticket: u64) -> io::Result<Option<String>> {
    match fs::read_to_string(dir.join(format!("{ticket}.draft"))) {
        Ok(text) => Ok(Some(text)),
        Err(e) if e.kind() == io::ErrorKind::NotFound => Ok(None),
        Err(e) => Err(e),
    }
}

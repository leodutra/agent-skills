use std::{fs, path::Path};

/// Drafts larger than this were never accepted by the editor.
pub const MAX_DRAFT_BYTES: usize = 64 * 1024;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct DraftTooLarge;

/// The saved draft for a ticket, if the user saved one.
///
/// # Errors
/// [`DraftTooLarge`] when the saved draft exceeds [`MAX_DRAFT_BYTES`].
pub fn saved_draft(dir: &Path, ticket: u64) -> Result<Option<String>, DraftTooLarge> {
    match fs::read_to_string(dir.join(format!("{ticket}.draft"))) {
        Ok(text) if text.len() > MAX_DRAFT_BYTES => Err(DraftTooLarge),
        Ok(text) => Ok(Some(text)),
        Err(_) => Ok(None),
    }
}

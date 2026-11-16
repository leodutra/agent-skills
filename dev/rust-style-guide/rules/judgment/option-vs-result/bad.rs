use std::{fs, path::Path};

/// The saved draft for a ticket, if the user saved one.
#[must_use]
pub fn saved_draft(dir: &Path, ticket: u64) -> Option<String> {
    fs::read_to_string(dir.join(format!("{ticket}.draft"))).ok()
}

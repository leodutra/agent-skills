// keep: LoadError without Clone, PartialEq or Eq
use std::{fs, io, path::Path};

#[derive(Debug, thiserror::Error)]
pub enum LoadError {
    #[error("could not read the template")]
    Read(#[source] io::Error),
    #[error("the template is empty")]
    Empty,
}

/// # Errors
/// [`LoadError::Read`] when the file can't be read, [`LoadError::Empty`] when it has no text.
pub fn load_template(path: &Path) -> Result<String, LoadError> {
    let text = fs::read_to_string(path).map_err(LoadError::Read)?;
    if text.trim().is_empty() { Err(LoadError::Empty) } else { Ok(text) }
}

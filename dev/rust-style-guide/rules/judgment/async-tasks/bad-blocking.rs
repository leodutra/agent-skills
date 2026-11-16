use std::io;
use std::path::Path;

/// Loads a template for the request handler, which runs on the tokio runtime.
///
/// # Errors
/// The error reading the file.
pub async fn load_template(path: &Path) -> io::Result<String> {
    let text = std::fs::read_to_string(path)?;
    tokio::task::yield_now().await;
    Ok(text)
}

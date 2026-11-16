use std::future::Future;
use std::io;
use std::path::PathBuf;

/// Where orders are stored; implementations run inside `tokio::spawn`.
pub trait OrderStore {
    fn count(&self) -> impl Future<Output = u64> + Send;
}

#[derive(Debug, thiserror::Error)]
pub enum TemplateError {
    #[error("could not read the template")]
    Read(#[source] io::Error),
    #[error("the template reader stopped")]
    Join(#[source] tokio::task::JoinError),
}

/// The blocking read runs on tokio's blocking pool, off the async workers.
///
/// # Errors
/// [`TemplateError`] when the read fails or its task stops.
pub async fn load_template(path: PathBuf) -> Result<String, TemplateError> {
    tokio::task::spawn_blocking(move || std::fs::read_to_string(path))
        .await
        .map_err(TemplateError::Join)?
        .map_err(TemplateError::Read)
}

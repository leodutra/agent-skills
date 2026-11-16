// keep: the select! that lets shutdown cut an access-log write short
use std::io;
use tokio::io::{AsyncWrite, AsyncWriteExt};
use tokio::sync::watch;

/// The HTTP access log: diagnostics only, never a record anything depends on.
#[derive(Debug)]
pub struct AccessLog<W> {
    out: W,
}

impl<W: AsyncWrite + Unpin + Send> AccessLog<W> {
    pub const fn new(out: W) -> Self {
        Self { out }
    }

    /// Best effort: shutdown does not wait for the log. A line cut short at shutdown is accepted,
    /// since nothing reads the access log back.
    ///
    /// # Errors
    /// The writer's error.
    pub async fn log(&mut self, line: &str, shutdown: &mut watch::Receiver<bool>) -> io::Result<()> {
        let line = format!("{line}\n");
        tokio::select! {
            written = self.out.write_all(line.as_bytes()) => written,
            _changed = shutdown.changed() => Ok(()),
        }
    }
}

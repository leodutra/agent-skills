use std::io;
use tokio::io::{AsyncWrite, AsyncWriteExt};
use tokio::sync::watch;

/// Appends one line per ledger entry; the file is the ledger of record.
#[derive(Debug)]
pub struct LedgerWriter<W> {
    out: W,
}

impl<W: AsyncWrite + Unpin + Send> LedgerWriter<W> {
    pub const fn new(out: W) -> Self {
        Self { out }
    }

    /// # Errors
    /// The writer's error.
    pub async fn append(&mut self, entry: &str, shutdown: &mut watch::Receiver<bool>) -> io::Result<()> {
        let line = format!("{entry}\n");
        tokio::select! {
            written = self.out.write_all(line.as_bytes()) => written,
            _changed = shutdown.changed() => Ok(()),
        }
    }
}

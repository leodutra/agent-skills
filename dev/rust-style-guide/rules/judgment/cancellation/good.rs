use std::io;
use tokio::io::{AsyncWrite, AsyncWriteExt};

/// Appends one line per ledger entry; the file is the ledger of record.
#[derive(Debug)]
pub struct LedgerWriter<W> {
    out: W,
}

impl<W: AsyncWrite + Unpin + Send> LedgerWriter<W> {
    pub const fn new(out: W) -> Self {
        Self { out }
    }

    /// Writes the whole line before returning. Shutdown is checked by the caller between
    /// entries, never in the middle of one.
    ///
    /// # Errors
    /// The writer's error.
    pub async fn append(&mut self, entry: &str) -> io::Result<()> {
        let line = format!("{entry}\n");
        self.out.write_all(line.as_bytes()).await?;
        self.out.flush().await
    }
}

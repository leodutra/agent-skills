//! The ledger file: one JSON line per posted entry, and the running balance.
use std::time::Duration;

use tokio::fs::File;
use tokio::io::AsyncWriteExt;
use tokio::sync::{mpsc, watch};

use crate::domain::ledger::{Cents, Entry};

#[derive(Debug, thiserror::Error)]
pub enum LedgerError {
    #[error("Could not encode the entry.")]
    Encode(#[from] serde_json::Error),
    #[error("Could not write the ledger.")]
    Io(#[from] std::io::Error),
    #[error("The balance would overflow.")]
    Overflow,
}

#[derive(Debug)]
pub struct LedgerWriter {
    file: File,
    balance: Cents,
}

impl LedgerWriter {
    pub const fn new(file: File, balance: Cents) -> Self {
        Self { file, balance }
    }

    /// Posts one entry: updates the balance, then appends the entry's line durably.
    pub async fn post(&mut self, entry: &Entry) -> Result<Cents, LedgerError> {
        self.balance = self.balance.checked_add(entry.amount()).ok_or(LedgerError::Overflow)?;
        let mut line = serde_json::to_vec(entry)?;
        line.push(b'\n');
        self.file.write_all(&line).await?;
        self.file.sync_data().await?;
        Ok(self.balance)
    }
}

/// Posts queued entries until the queue closes or shutdown is signalled.
pub async fn run(
    mut writer: LedgerWriter,
    mut queue: mpsc::Receiver<Entry>,
    mut shutdown: watch::Receiver<bool>,
) -> Result<(), LedgerError> {
    loop {
        let Some(entry) = queue.recv().await else {
            return Ok(());
        };
        tokio::select! {
            _ = shutdown.changed() => return Ok(()),
            posted = writer.post(&entry) => {
                posted?;
            }
        }
    }
}

/// Starts the ledger writer in the background.
pub fn spawn(writer: LedgerWriter, queue: mpsc::Receiver<Entry>, shutdown: watch::Receiver<bool>) {
    tokio::spawn(run(writer, queue, shutdown));
}

/// Appends one line to the access log. Best effort by design: a timeout can leave the last
/// line truncated, which the log reader skips, and losing a line is acceptable for this log.
pub async fn log_access(log: &mut File, line: &str) {
    match tokio::time::timeout(Duration::from_millis(50), log.write_all(line.as_bytes())).await {
        Ok(Ok(())) => {}
        Ok(Err(error)) => tracing::warn!(%error, "access log write failed"),
        Err(_elapsed) => tracing::warn!("access log write timed out"),
    }
}

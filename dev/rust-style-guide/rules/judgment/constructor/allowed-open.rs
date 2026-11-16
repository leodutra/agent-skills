// keep: the fallible OrderLog::open constructor
use std::fs::{File, OpenOptions};
use std::io;
use std::path::Path;

/// An append-only file of orders.
#[derive(Debug)]
pub struct OrderLog {
    file: File,
}

impl OrderLog {
    /// # Errors
    /// The error opening or creating the file.
    pub fn open(path: &Path) -> io::Result<Self> {
        let file = OpenOptions::new().create(true).append(true).open(path)?;
        Ok(Self { file })
    }

    /// # Errors
    /// The error syncing the file.
    pub fn sync(&self) -> io::Result<()> {
        self.file.sync_all()
    }
}

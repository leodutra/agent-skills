//! Blob storage on the local filesystem: one file per key under a root directory.
use std::fs;
use std::io;
use std::path::PathBuf;

/// Where archived blobs live. Keys are written by our own code, never by users.
pub trait BlobStore {
    /// Stores `bytes` under `key`, replacing what was there.
    fn put(&mut self, key: &str, bytes: &[u8]) -> io::Result<()>;
    /// The bytes under `key`; `Ok(None)` when nothing was stored there.
    fn get(&self, key: &str) -> io::Result<Option<Vec<u8>>>;
}

#[derive(Debug)]
pub struct FsBlobStore {
    root: PathBuf,
}

impl FsBlobStore {
    pub fn open(root: PathBuf) -> io::Result<Self> {
        fs::create_dir_all(&root)?;
        Ok(Self { root })
    }
}

impl BlobStore for FsBlobStore {
    fn put(&mut self, key: &str, bytes: &[u8]) -> io::Result<()> {
        // Write aside, then rename: a reader never sees half a blob.
        let tmp = self.root.join(format!("{key}.tmp"));
        fs::write(&tmp, bytes)?;
        fs::rename(tmp, self.root.join(key))
    }

    fn get(&self, key: &str) -> io::Result<Option<Vec<u8>>> {
        match fs::read(self.root.join(key)) {
            Ok(bytes) => Ok(Some(bytes)),
            Err(e) if e.kind() == io::ErrorKind::NotFound => Ok(None),
            Err(e) => Err(e),
        }
    }
}

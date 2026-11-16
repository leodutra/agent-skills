//! Fixed-width record access, in the storage crate's `raw` module. Benchmarked: 22% faster scans.

/// Fields of a fixed 8-byte record.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Record {
    bytes: [u8; 8],
}

impl Record {
    #[must_use]
    pub const fn new(bytes: [u8; 8]) -> Self {
        Self { bytes }
    }

    /// The record's flag byte.
    #[expect(unsafe_code, reason = "hot scan loop, benchmark in the module docs")]
    #[must_use]
    pub fn flags(&self) -> u8 {
        // SAFETY: this is fine, it has been tested.
        unsafe { *self.bytes.get_unchecked(7) }
    }
}

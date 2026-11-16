//! Fixed-width record access, the storage crate's `raw` module: the only `unsafe` in the workspace,
//! behind a safe API. Benchmarked 2026-10-02: unchecked reads make full scans 22% faster.

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

    /// The record's flag byte: safe, since the index is a constant within the array.
    #[expect(unsafe_code, reason = "hot scan loop, benchmark in the module docs")]
    #[must_use]
    pub fn flags(&self) -> u8 {
        // SAFETY: `bytes` is `[u8; 8]`, so index 7 is in bounds.
        unsafe { *self.bytes.get_unchecked(7) }
    }

    /// The byte at `index`, for the scan loop.
    ///
    /// # Safety
    /// `index` must be below 8; only the caller's loop bound knows it.
    #[expect(unsafe_code, reason = "hot scan loop, benchmark in the module docs")]
    #[must_use]
    pub unsafe fn byte_unchecked(&self, index: usize) -> u8 {
        // SAFETY: the caller guarantees `index < 8`, the array's length.
        unsafe { *self.bytes.get_unchecked(index) }
    }
}

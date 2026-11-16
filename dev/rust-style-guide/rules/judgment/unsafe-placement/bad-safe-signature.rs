//! A byte buffer with fast access, for the packet parser.

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Packet {
    bytes: Vec<u8>,
}

impl Packet {
    #[must_use]
    pub const fn new(bytes: Vec<u8>) -> Self {
        Self { bytes }
    }

    /// The byte at `index`. Callers pass an index below `len()`.
    #[expect(unsafe_code, reason = "the parser reads every byte in a hot loop")]
    #[must_use]
    pub fn byte_at(&self, index: usize) -> u8 {
        // SAFETY: callers pass an index below `len()`.
        unsafe { *self.bytes.get_unchecked(index) }
    }

    #[must_use]
    pub fn len(&self) -> usize {
        self.bytes.len()
    }

    #[must_use]
    pub fn is_empty(&self) -> bool {
        self.bytes.is_empty()
    }
}

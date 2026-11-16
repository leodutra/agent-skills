use std::str::FromStr;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Size {
    pub width: u32,
    pub height: u32,
}

impl Size {
    /// Two values make a size: a constructor, not a conversion.
    #[must_use]
    pub const fn new(width: u32, height: u32) -> Self {
        Self { width, height }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, clap::ValueEnum)]
pub enum Priority {
    Low,
    High,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct UnknownPriority;

/// Accepts the same names `ValueEnum` uses.
impl FromStr for Priority {
    type Err = UnknownPriority;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "low" => Ok(Self::Low),
            "high" => Ok(Self::High),
            _ => Err(UnknownPriority),
        }
    }
}

/// The header of a capture file, written in the recording machine's byte order.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Header {
    pub version: u16,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ByteOrder {
    Little,
    Big,
}

impl Header {
    /// The byte order is a choice the bytes can't state, so it's a named decoder.
    #[must_use]
    pub const fn decode(bytes: [u8; 2], order: ByteOrder) -> Self {
        let version = match order {
            ByteOrder::Little => u16::from_le_bytes(bytes),
            ByteOrder::Big => u16::from_be_bytes(bytes),
        };
        Self { version }
    }
}

/// The header of a capture file: the format writes it in the byte order of the machine that
/// recorded it, and version 2 added a flags field.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Header {
    pub version: u16,
    pub flags: u16,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ShortHeader;

impl TryFrom<&[u8]> for Header {
    type Error = ShortHeader;

    fn try_from(bytes: &[u8]) -> Result<Self, Self::Error> {
        match bytes {
            [v0, v1, f0, f1, ..] => Ok(Self {
                version: u16::from_le_bytes([*v0, *v1]),
                flags: u16::from_le_bytes([*f0, *f1]),
            }),
            _ => Err(ShortHeader),
        }
    }
}

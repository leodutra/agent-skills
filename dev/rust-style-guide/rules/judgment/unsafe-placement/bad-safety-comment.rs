//! The `sensor` crate's `driver` module: the workspace's only `unsafe`, wrapping the vendor's C
//! driver (no Rust implementation exists), behind a safe API.

#[expect(unsafe_code, reason = "FFI to the vendor's C driver")]
unsafe extern "C" {
    /// Reads channel `channel`; the driver's contract: `channel` must be below 4.
    fn sensor_read_celsius(channel: u32) -> i32;
}

/// One of the board's four channels.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Channel(u32);

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct NoSuchChannel;

impl Channel {
    /// # Errors
    /// [`NoSuchChannel`] unless `n` is below 4.
    pub const fn try_new(n: u32) -> Result<Self, NoSuchChannel> {
        if n < 4 { Ok(Self(n)) } else { Err(NoSuchChannel) }
    }
}

#[expect(unsafe_code, reason = "FFI to the vendor's C driver")]
#[must_use]
pub fn read_celsius(channel: Channel) -> i32 {
    // SAFETY: the driver is well tested.
    unsafe { sensor_read_celsius(channel.0) }
}

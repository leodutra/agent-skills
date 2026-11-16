//! The `sensor` crate's `driver` module: the workspace's only `unsafe`, wrapping the vendor's C
//! driver (no Rust implementation exists).

#[expect(unsafe_code, reason = "FFI to the vendor's C driver")]
unsafe extern "C" {
    /// Reads channel `channel`; the driver's contract: `channel` must be below 4, or it reads out
    /// of bounds.
    fn sensor_read_celsius(channel: u32) -> i32;
}

/// The temperature on `channel`. Callers pass a channel below 4.
#[expect(unsafe_code, reason = "FFI to the vendor's C driver")]
#[must_use]
pub fn read_celsius(channel: u32) -> i32 {
    // SAFETY: callers pass a channel below 4, as the driver requires.
    unsafe { sensor_read_celsius(channel) }
}

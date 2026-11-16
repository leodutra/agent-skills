fn checked_retries(n: u8) -> Result<u8, ()> {
    if n <= 10 { Ok(n) } else { Err(()) }
}

/// Whether `n` is an accepted retry count.
#[must_use]
pub fn retries_accepted(n: u8) -> bool {
    checked_retries(n).is_ok()
}

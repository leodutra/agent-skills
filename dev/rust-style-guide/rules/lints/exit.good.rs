#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Failed {
    pub code: i32,
}

/// # Errors
/// Always: the caller decides how to stop.
pub const fn fail(code: i32) -> Result<(), Failed> {
    Err(Failed { code })
}

/// Converts whole dollars to cents.
macro_rules! cents {
    ($dollars:expr) => {
        $dollars * 100
    };
}

#[must_use]
pub const fn shipping_cents(express: bool) -> u64 {
    if express { cents!(12) } else { cents!(5) }
}

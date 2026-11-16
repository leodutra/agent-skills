use tokio::sync::Mutex;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum UsageError {
    #[error("usage: app <port>")]
    MissingPort,
    #[error("usage: app <port>: {0:?} is not a port")]
    BadPort(String),
}

/// # Errors
/// [`UsageError`] for a missing or unparsable port, which `main` prints with exit code 2.
pub fn port_from_args(args: &[String]) -> Result<u16, UsageError> {
    let arg = args.get(1).ok_or(UsageError::MissingPort)?;
    arg.parse().map_err(|_e: std::num::ParseIntError| UsageError::BadPort(arg.clone()))
}

/// The `n`th word, or `None` when the line is shorter.
#[must_use]
pub fn nth_word(line: &str, n: usize) -> Option<&str> {
    line.split_whitespace().nth(n)
}

#[derive(Debug, Default)]
pub struct Stats {
    pub orders: u64,
    pub revenue_cents: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct StatsOverflow;

/// Computes both totals first, so nothing can panic while the lock is held.
///
/// # Errors
/// [`StatsOverflow`] when a total would overflow.
pub async fn record_sale(stats: &Mutex<Stats>, cents: u64) -> Result<(), StatsOverflow> {
    let mut stats = stats.lock().await;
    let orders = stats.orders.checked_add(1).ok_or(StatsOverflow)?;
    let revenue = stats.revenue_cents.checked_add(cents).ok_or(StatsOverflow)?;
    stats.orders = orders;
    stats.revenue_cents = revenue;
    Ok(())
}

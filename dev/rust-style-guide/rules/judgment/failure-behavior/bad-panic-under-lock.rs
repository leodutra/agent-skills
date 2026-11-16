use tokio::sync::Mutex;

#[derive(Debug, Default)]
pub struct Stats {
    pub orders: u64,
    pub revenue_cents: u64,
}

/// Records a sale. `Stats` is shared across request handlers.
pub async fn record_sale(stats: &Mutex<Stats>, cents: u64) {
    let mut stats = stats.lock().await;
    stats.orders += 1;
    stats.revenue_cents += cents;
}

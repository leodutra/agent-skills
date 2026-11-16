use std::future::Future;

/// Where orders are stored. The server calls these from tasks it spawns with `tokio::spawn` on its
/// multithreaded runtime.
pub trait OrderStore {
    fn count(&self) -> impl Future<Output = u64>;
}

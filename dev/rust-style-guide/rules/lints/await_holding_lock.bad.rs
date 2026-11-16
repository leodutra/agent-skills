// expect: clippy::await_holding_lock
// also: clippy::disallowed_types clippy::future_not_send
use std::sync::Mutex;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Poisoned;

/// # Errors
/// [`Poisoned`] when the lock is poisoned.
pub async fn bump(counter: &Mutex<u32>) -> Result<u32, Poisoned> {
    let Ok(mut guard) = counter.lock() else { return Err(Poisoned) };
    std::future::ready(()).await;
    *guard += 1;
    Ok(*guard)
}

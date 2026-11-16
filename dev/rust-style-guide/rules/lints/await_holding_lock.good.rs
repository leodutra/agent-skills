#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Poisoned;

/// # Errors
/// [`Poisoned`] when the lock is poisoned.
#[expect(clippy::disallowed_types, reason = "infrastructure; a domain crate holds no Mutex")]
pub async fn bump(counter: &std::sync::Mutex<u32>) -> Result<u32, Poisoned> {
    let next = {
        let Ok(mut guard) = counter.lock() else { return Err(Poisoned) };
        *guard += 1;
        *guard
    };
    std::future::ready(()).await;
    Ok(next)
}

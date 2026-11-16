// Allowed: a non-Send future deliberately run only on a local executor, under a reasoned #[expect].
use std::rc::Rc;

#[expect(clippy::future_not_send, reason = "runs only on the UI thread's local executor")]
pub async fn total(parts: Rc<[u32]>) -> u32 {
    std::future::ready(()).await;
    parts.iter().sum()
}

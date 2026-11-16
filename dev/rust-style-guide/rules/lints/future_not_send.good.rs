use std::sync::Arc;

pub async fn total(parts: Arc<[u32]>) -> u32 {
    std::future::ready(()).await;
    parts.iter().sum()
}

// expect: clippy::future_not_send
use std::rc::Rc;

pub async fn total(parts: Rc<[u32]>) -> u32 {
    std::future::ready(()).await;
    parts.iter().sum()
}

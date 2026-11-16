// expect: clippy::await_holding_refcell_ref
// also: clippy::disallowed_types clippy::future_not_send
use std::cell::RefCell;

pub async fn bump(counter: &RefCell<u32>) -> u32 {
    let mut value = counter.borrow_mut();
    std::future::ready(()).await;
    *value += 1;
    *value
}

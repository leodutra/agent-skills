// expect: clippy::let_underscore_future
pub async fn flush() {}

pub fn shutdown() {
    let _ = flush();
}

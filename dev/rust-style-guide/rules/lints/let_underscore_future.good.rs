pub async fn flush() {}

pub async fn shutdown() {
    flush().await;
}

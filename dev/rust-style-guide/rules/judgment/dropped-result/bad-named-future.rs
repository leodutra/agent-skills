/// Flushes the outbox to the mail server.
pub async fn flush_outbox() {}

/// Called when a user logs out.
pub fn on_logout() {
    let _flush = flush_outbox();
}

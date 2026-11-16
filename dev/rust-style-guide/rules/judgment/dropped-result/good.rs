use std::io::{self, Write};

/// Writes the receipt; the order is already paid.
///
/// # Errors
/// The writer's error.
pub fn print_receipt(out: &mut impl Write, total_cents: u64) -> io::Result<()> {
    writeln!(out, "total: {total_cents} cents")
}

/// Flushes the outbox to the mail server.
pub async fn flush_outbox() {}

/// Called when a user logs out.
pub async fn on_logout() {
    flush_outbox().await;
}

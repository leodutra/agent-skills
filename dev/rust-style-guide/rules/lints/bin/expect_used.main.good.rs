// Allowed: main.rs expect() with a clear message for an environment startup failure, under its #[expect].
use std::net::TcpListener;

#[expect(clippy::expect_used, reason = "startup: without the port the service cannot run")]
fn main() {
    let listener = TcpListener::bind("127.0.0.1:0").expect("bind a local port");
    drop(listener);
}

//! acme-measure CLI: checks a sampling interval and prints it.
use acme_measure::{DEFAULT_INTERVAL, Interval};

#[expect(
    clippy::expect_used,
    reason = "bootstrap: a missing or malformed argument stops the CLI with a clear message"
)]
#[expect(clippy::print_stdout, reason = "the CLI reports its result to stdout")]
fn main() {
    let raw = std::env::args()
        .nth(1)
        .expect("usage: acme-measure <interval in ms>");
    let interval: Interval = raw
        .parse()
        .expect("the interval must be a whole, non-zero number of milliseconds");
    println!("sampling every {interval} ms (default {DEFAULT_INTERVAL} ms)");
}

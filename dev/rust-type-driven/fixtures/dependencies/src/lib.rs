pub use serde::Serialize;

pub fn digits(n: u64) -> String { itoa::Buffer::new().format(n).to_string() }

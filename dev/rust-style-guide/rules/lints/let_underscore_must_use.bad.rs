// expect: clippy::let_underscore_must_use
use std::fmt::Write;

pub fn label(out: &mut String, n: u32) {
    let _ = write!(out, "#{n}");
}

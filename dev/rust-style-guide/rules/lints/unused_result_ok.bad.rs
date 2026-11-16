// expect: clippy::unused_result_ok
use std::fmt::Write;

pub fn label(out: &mut String, n: u32) {
    write!(out, "#{n}").ok();
}

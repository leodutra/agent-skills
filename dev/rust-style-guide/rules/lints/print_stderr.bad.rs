// expect: clippy::print_stderr
pub fn warn(total: u32) {
    eprintln!("total too high: {total}");
}

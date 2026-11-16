// expect: clippy::exit
pub fn fail(code: i32) -> ! {
    std::process::exit(code)
}

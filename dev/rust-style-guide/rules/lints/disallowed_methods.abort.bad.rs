// expect: clippy::disallowed_methods std::process::abort
pub fn give_up() -> ! {
    std::process::abort()
}

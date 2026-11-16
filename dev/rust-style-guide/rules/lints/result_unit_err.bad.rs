// expect: clippy::result_unit_err
pub fn percent(n: u8) -> Result<u8, ()> {
    if n <= 100 { Ok(n) } else { Err(()) }
}

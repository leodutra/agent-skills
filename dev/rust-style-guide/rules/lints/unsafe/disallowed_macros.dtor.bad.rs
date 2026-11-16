// expect: clippy::disallowed_macros dtor::dtor
#[dtor::dtor(unsafe)]
fn flush_cache() {}

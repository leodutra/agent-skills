// expect: clippy::disallowed_macros ctor::ctor
#[ctor::ctor(unsafe)]
fn warm_cache() {}

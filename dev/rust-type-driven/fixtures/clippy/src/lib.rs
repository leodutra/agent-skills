//! One violation per lint of Enforce with Tools. A flagged line ends with `expect: <lint>`.

pub fn unsafe_block() -> u8 { unsafe { std::mem::zeroed() } } // expect: unsafe_code, undocumented_unsafe_blocks
pub fn unwraps(x: Option<u8>) -> u8 { x.unwrap() } // expect: unwrap_used
pub fn expects(x: Option<u8>) -> u8 { x.expect("present") } // expect: expect_used
pub fn panics() { panic!("no") } // expect: panic
pub fn todos() -> u8 { todo!() } // expect: todo
pub fn unimplementeds() -> u8 { unimplemented!() } // expect: unimplemented
pub fn unreachables() -> u8 { unreachable!() } // expect: unreachable

#[derive(Debug)]
pub enum Three { A, B, C }
pub fn wildcard(t: &Three) -> u8 {
    match t {
        Three::A => 1,
        _ => 2, // expect: wildcard_enum_match_arm
    }
}
#[derive(Debug)]
pub enum Two { A, B }
pub fn single_wildcard(t: &Two) -> u8 {
    match t {
        Two::A => 1,
        _ => 2, // expect: match_wildcard_for_single_variants
    }
}

pub async fn lock_across_await(m: &std::sync::Mutex<u8>) -> u8 { // expect: future_not_send, disallowed_types
    let g = m.lock().unwrap_or_else(std::sync::PoisonError::into_inner); // expect: await_holding_lock
    std::future::ready(()).await;
    *g
}
pub async fn borrow_across_await(c: &std::cell::RefCell<u8>) -> u8 { // expect: future_not_send, disallowed_types
    let b = c.borrow(); // expect: await_holding_refcell_ref
    std::future::ready(()).await;
    *b
}

pub fn by_value(v: Vec<u8>) -> usize { v.len() } // expect: needless_pass_by_value
pub fn clones(s: &str) -> String { let t = s.to_string(); t.clone() } // expect: redundant_clone

#[derive(Debug)]
pub struct Flags { pub a: bool, pub b: bool, pub c: bool, pub d: bool } // expect: struct_excessive_bools
pub fn flags(a: bool, b: bool, c: bool, d: bool) -> bool { a && b && c && d } // expect: fn_params_excessive_bools

#[derive(Debug)]
pub struct Holder(pub std::sync::Mutex<u8>); // expect: disallowed_types
pub fn stamp() -> std::time::Instant { std::time::Instant::now() } // expect: disallowed_methods

pub struct NoDebug(pub u8); // expect: missing_debug_implementations
#[derive(Debug, Clone, PartialEq)] // expect: derive_partial_eq_without_eq
pub struct NoEq(u8);

#[allow(dead_code)] // expect: allow_attributes, allow_attributes_without_reason
fn quiet() {}

// Near misses: none of these may be flagged.
#[expect(clippy::needless_pass_by_value, reason = "the caller hands over ownership on purpose")]
pub fn owned(v: Vec<u8>) -> usize { v.len() }
pub fn borrowed(v: &[u8]) -> usize { v.len() }
pub fn exhaustive(t: &Two) -> u8 {
    match t {
        Two::A => 1,
        Two::B => 2,
    }
}
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Ratio(f64);
pub struct Secret(String);
impl Secret {
    #[must_use]
    pub fn expose(&self) -> &str { &self.0 }
}
impl std::fmt::Debug for Secret {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result { f.write_str("Secret(..)") }
}
#[must_use]
pub fn add(a: u32, b: u32) -> Option<u32> { a.checked_add(b) }

#[cfg(test)]
mod tests {
    #[test]
    fn unwrap_is_allowed_in_tests() { assert_eq!(super::add(1, 2).unwrap(), 3); }
}

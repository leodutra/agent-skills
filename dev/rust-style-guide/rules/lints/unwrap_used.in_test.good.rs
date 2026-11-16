// Allowed: unwrap(), expect() and panic! in #[cfg(test)] code.
#[must_use]
pub const fn double(n: u32) -> Option<u32> {
    n.checked_mul(2)
}

#[cfg(test)]
mod tests {
    #[test]
    fn doubles() {
        assert_eq!(super::double(2).unwrap(), 4);
        assert_eq!(super::double(3).expect("small input"), 6);
        if super::double(u32::MAX).is_some() {
            panic!("overflow went unnoticed");
        }
    }
}

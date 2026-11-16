// expect: clippy::todo
// also: clippy::unimplemented clippy::unreachable
#[must_use]
pub const fn double(n: u32) -> u32 {
    n.saturating_mul(2)
}

#[cfg(test)]
mod tests {
    #[test]
    fn placeholders_in_tests() {
        if super::double(1) == 0 {
            todo!()
        }
        if super::double(2) == 0 {
            unimplemented!()
        }
        if super::double(3) == 0 {
            unreachable!()
        }
    }
}

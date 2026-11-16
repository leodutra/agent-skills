/// Width and height in pixels.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Size(pub u32, pub u32);

#[must_use]
pub const fn area(size: Size) -> u64 {
    size.0 as u64 * size.1 as u64
}

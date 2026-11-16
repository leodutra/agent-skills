#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Emphasis {
    Bold,
    Italic,
    Underline,
    Strike,
}

#[must_use]
pub fn flags(emphasis: &[Emphasis]) -> u8 {
    let mut bits = 0;
    for e in emphasis {
        bits |= match e {
            Emphasis::Bold => 1,
            Emphasis::Italic => 2,
            Emphasis::Underline => 4,
            Emphasis::Strike => 8,
        };
    }
    bits
}

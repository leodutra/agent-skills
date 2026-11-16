// keep: Reading deriving PartialEq without Eq over an f64
/// A sensor reading, kept as the device reports it: IEEE 754, so a failed read is NaN and never
/// equals anything, which is the comparison the alerting code relies on.
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd)]
pub struct Reading {
    pub celsius: f64,
}

use std::fmt;

/// The payment provider's API key: Debug is redacted, and there is no Display or Serialize.
#[derive(Clone, PartialEq, Eq)]
pub struct ApiKey(String);

impl fmt::Debug for ApiKey {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("ApiKey(***)")
    }
}

/// Declared in the domain's order, so the derived `Ord` is Low < Medium < High < Critical.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Severity {
    Low,
    Medium,
    High,
    Critical,
}

/// A bus stop's identity: integer microdegrees, so `Eq` and `Hash` hold for real.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct StopId {
    pub latitude_micro: i32,
    pub longitude_micro: i32,
}

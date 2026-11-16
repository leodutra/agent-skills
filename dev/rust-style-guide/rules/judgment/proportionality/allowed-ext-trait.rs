// keep: the DurationExt extension trait and its impl for Duration
use std::time::Duration;

/// Billing rounds every started minute up.
pub trait DurationExt {
    fn billed_minutes(&self) -> u64;
}

impl DurationExt for Duration {
    fn billed_minutes(&self) -> u64 {
        self.as_secs().div_ceil(60)
    }
}

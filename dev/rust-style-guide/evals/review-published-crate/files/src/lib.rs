//! acme-measure: sensor readings, sampling intervals and the reading store.
use std::{fmt, num::NonZeroU32, num::ParseIntError, str::FromStr};

/// A sensor's id; any u32 is fine.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub struct SensorId(pub u32);

/// Milliseconds since the Unix epoch.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub struct Timestamp(pub u64);

/// A sampling interval in milliseconds; never zero.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub struct Interval(NonZeroU32);

/// `Interval::try_new`'s only failure.
#[derive(Debug, Clone, Copy, PartialEq, Eq, thiserror::Error)]
#[error("interval must be non-zero")]
pub struct ZeroInterval;

/// Text adds a syntax failure in front of the constructor's.
#[non_exhaustive]
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ParseIntervalError {
    #[error("invalid interval: {0}")]
    Syntax(#[from] ParseIntError),
    #[error(transparent)]
    Zero(#[from] ZeroInterval),
}

impl Interval {
    pub const fn try_new(ms: u32) -> Result<Self, ZeroInterval> {
        match NonZeroU32::new(ms) {
            Some(ms) => Ok(Self(ms)),
            None => Err(ZeroInterval),
        }
    }

    /// Literals only: called in a const item, an invalid value fails compilation.
    #[must_use]
    #[expect(
        clippy::panic,
        reason = "a compile-time literal: an invalid value fails compilation"
    )]
    pub const fn literal(ms: u32) -> Self {
        match Self::try_new(ms) {
            Ok(interval) => interval,
            Err(ZeroInterval) => panic!("interval must be non-zero"),
        }
    }

    #[must_use]
    pub const fn get(self) -> u32 {
        self.0.get()
    }
}

pub const DEFAULT_INTERVAL: Interval = Interval::literal(1_000);

impl TryFrom<u32> for Interval {
    type Error = ZeroInterval;

    fn try_from(ms: u32) -> Result<Self, Self::Error> {
        Self::try_new(ms)
    }
}

impl From<Interval> for u32 {
    fn from(interval: Interval) -> Self {
        interval.get()
    }
}

impl FromStr for Interval {
    type Err = ParseIntervalError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        Ok(Self::try_new(s.parse()?)?)
    }
}

impl fmt::Display for Interval {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.0.fmt(f)
    }
}

/// The secret token readings are uploaded with: 32 hex digits.
#[derive(Clone)]
pub struct UploadToken(String);

/// `UploadToken::try_new`'s only failure.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
#[error("invalid upload token {0:?}: expected 32 hex digits")]
pub struct InvalidToken(String);

impl UploadToken {
    pub fn try_new(raw: &str) -> Result<Self, InvalidToken> {
        let raw = raw.trim();
        if raw.len() == 32 && raw.bytes().all(|b| b.is_ascii_hexdigit()) {
            Ok(Self(raw.to_ascii_lowercase()))
        } else {
            Err(InvalidToken(raw.to_owned()))
        }
    }

    /// For the upload's Authorization header only.
    #[must_use]
    pub fn expose(&self) -> &str {
        &self.0
    }
}

impl fmt::Debug for UploadToken {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("UploadToken(..)")
    }
}

/// Which readings a query covers.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Window {
    /// Every reading.
    All,
    /// Readings taken from `start` up to, not including, `end`; `end` is after `start`.
    Between { start: Timestamp, end: Timestamp },
}

impl Window {
    #[must_use]
    pub const fn contains(self, at: Timestamp) -> bool {
        match self {
            Self::All => true,
            Self::Between { start, end } => start.0 <= at.0 && at.0 < end.0,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Reading {
    pub sensor: SensorId,
    pub taken_at: Timestamp,
    pub millivolts: i32,
}

#[derive(Debug, thiserror::Error)]
#[error("reading store unavailable")]
pub struct StoreError(#[source] pub std::io::Error);

/// Where readings are kept. Other teams implement it over their own databases.
pub trait ReadingStore {
    /// A sensor's newest reading: `Ok(None)` when it has none yet, `Err` when the store fails.
    fn latest(&self, sensor: SensorId) -> Result<Option<Reading>, StoreError>;

    /// A sensor's readings inside `window`, oldest first.
    fn within(&self, sensor: SensorId, window: Window) -> Result<Vec<Reading>, StoreError>;
}

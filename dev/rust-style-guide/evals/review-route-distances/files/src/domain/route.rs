//! Route legs and their lengths, for the delivery planner.
use std::cmp::Ordering;
use std::collections::HashSet;
use std::hash::{Hash, Hasher};
use std::ops::Add;

/// A distance in kilometres: finite and never negative.
#[derive(Debug, Clone, Copy)]
pub struct Kilometres(f64);

#[derive(Debug, Clone, Copy, PartialEq, Eq, thiserror::Error)]
pub enum InvalidDistance {
    #[error("distance must be a finite number")]
    NotFinite,
    #[error("distance must not be negative")]
    Negative,
}

impl Kilometres {
    pub const ZERO: Self = Self(0.0);

    pub fn try_new(km: f64) -> Result<Self, InvalidDistance> {
        if !km.is_finite() {
            return Err(InvalidDistance::NotFinite);
        }
        if km < 0.0 {
            return Err(InvalidDistance::Negative);
        }
        Ok(Self(km))
    }

    #[must_use]
    pub const fn get(self) -> f64 {
        self.0
    }
}

// try_new rejects NaN, so every value equals itself.
impl PartialEq for Kilometres {
    fn eq(&self, other: &Self) -> bool {
        self.0 == other.0
    }
}

impl Eq for Kilometres {}

impl PartialOrd for Kilometres {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for Kilometres {
    fn cmp(&self, other: &Self) -> Ordering {
        self.0.total_cmp(&other.0)
    }
}

impl Hash for Kilometres {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.0.to_bits().hash(state);
    }
}

impl Add for Kilometres {
    type Output = Self;

    fn add(self, rhs: Self) -> Self {
        Self(self.0 + rhs.0)
    }
}

/// A delivery stop.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, serde::Serialize, serde::Deserialize)]
#[serde(transparent)]
pub struct StopId(pub u32);

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Leg {
    pub from: StopId,
    pub to: StopId,
    pub length: Kilometres,
}

/// One GPS fix as the van's tracker reports it.
#[derive(Debug, Clone, Copy, PartialEq, serde::Deserialize)]
pub struct Fix {
    pub lat: f64,
    pub lon: f64,
}

// The tracker repeats fixes while the van stands still; we dedup them in a set.
impl Eq for Fix {}

impl Hash for Fix {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.lat.to_bits().hash(state);
        self.lon.to_bits().hash(state);
    }
}

#[must_use]
pub fn total(legs: &[Leg]) -> Kilometres {
    legs.iter().fold(Kilometres::ZERO, |sum, leg| sum + leg.length)
}

#[must_use]
pub fn longest(legs: &[Leg]) -> Option<&Leg> {
    legs.iter().max_by_key(|leg| leg.length)
}

/// The fixes in arrival order, each repeat dropped.
#[must_use]
pub fn dedup_fixes(fixes: &[Fix]) -> Vec<Fix> {
    let mut seen = HashSet::new();
    fixes.iter().copied().filter(|fix| seen.insert(*fix)).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rejects_nan() {
        assert_eq!(Kilometres::try_new(f64::NAN), Err(InvalidDistance::NotFinite));
    }

    #[test]
    fn rejects_negative() {
        assert_eq!(Kilometres::try_new(-1.0), Err(InvalidDistance::Negative));
    }

    #[test]
    fn accepts_a_distance() {
        assert_eq!(Kilometres::try_new(12.5).map(Kilometres::get), Ok(12.5));
    }
}

//! A refinement over `f64`: finite and never negative, so `Eq`, `Hash` and `Ord` hold.
//!
//! Arithmetic that can break the invariant is a `try_*` method, never an operator: two finite
//! values can sum to infinity, and `Add`'s `Output` can't say so.
//! ```compile_fail
//! use template::domain::km::Km;
//! let (a, b) = (Km::try_new(1.0).expect("finite"), Km::try_new(2.0).expect("finite"));
//! let sum = a + b;
//! ```
//! ```
//! use template::domain::km::Km;
//! let (a, b) = (Km::try_new(1.0).expect("finite"), Km::try_new(2.0).expect("finite"));
//! let sum = a.try_add(b);
//! ```
use std::cmp::Ordering;
use std::hash::{Hash, Hasher};

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Km(f64);

/// The constructor's only failure, so a unit struct.
#[derive(Debug, Clone, Copy, PartialEq, Eq, thiserror::Error)]
#[error("distance must be finite and not negative")]
pub struct InvalidKm;

impl Km {
    /// # Errors
    /// [`InvalidKm`] for NaN, an infinity or a negative distance.
    pub fn try_new(km: f64) -> Result<Self, InvalidKm> {
        if !km.is_finite() || km < 0.0 {
            return Err(InvalidKm);
        }
        // `-0.0` passes the check above; `abs` turns it into `0.0`: one zero, one hash.
        Ok(Self(km.abs()))
    }

    /// # Errors
    /// [`InvalidKm`] when the sum overflows to infinity.
    pub fn try_add(self, rhs: Self) -> Result<Self, InvalidKm> {
        Self::try_new(self.0 + rhs.0)
    }

    #[must_use]
    pub const fn get(self) -> f64 {
        self.0
    }
}

/// The constructor rejects NaN, so `a == a` for every `Km`.
impl Eq for Km {}

impl Hash for Km {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.0.to_bits().hash(state);
    }
}

impl PartialOrd for Km {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for Km {
    fn cmp(&self, other: &Self) -> Ordering {
        self.0.total_cmp(&other.0)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn accepts_a_distance_and_rejects_what_breaks_eq() {
        assert_eq!(Km::try_new(1.5).map(Km::get), Ok(1.5));
        assert_eq!(Km::try_new(f64::NAN), Err(InvalidKm));
        assert_eq!(Km::try_new(f64::INFINITY), Err(InvalidKm));
        assert_eq!(Km::try_new(-1.0), Err(InvalidKm));
        assert_eq!(
            Km::try_new(-0.0).map(|km| km.get().to_bits()),
            Ok(0.0_f64.to_bits())
        );
        assert_eq!(
            Km::try_new(f64::MAX).and_then(|a| a.try_add(a)),
            Err(InvalidKm)
        );
    }
}

//! A TryFrom constructor, tested once accepted and once per rejection reason: every mutant is caught.

#[derive(Debug, PartialEq)]
pub struct Age(u8);

#[derive(Debug, PartialEq)]
pub enum AgeError {
    Negative,
    TooOld,
}

impl TryFrom<i64> for Age {
    type Error = AgeError;

    fn try_from(years: i64) -> Result<Self, Self::Error> {
        if years < 0 {
            return Err(AgeError::Negative);
        }
        if years > 150 {
            return Err(AgeError::TooOld);
        }
        Ok(Self(years as u8))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn accepts_the_bounds() {
        assert_eq!(Age::try_from(0), Ok(Age(0)));
        assert_eq!(Age::try_from(150), Ok(Age(150)));
    }

    #[test]
    fn rejects_negative() {
        assert_eq!(Age::try_from(-1), Err(AgeError::Negative));
    }

    #[test]
    fn rejects_too_old() {
        assert_eq!(Age::try_from(151), Err(AgeError::TooOld));
    }
}

//! A FromStr constructor with an untested rejection guard: from_str is in the mutation scope.

#[derive(Debug, PartialEq)]
pub struct Level(u8);

impl std::str::FromStr for Level {
    type Err = ();

    fn from_str(raw: &str) -> Result<Self, Self::Err> {
        let n: u8 = raw.parse().map_err(|_| ())?;
        if n > 9 { // expect: missed-mutant
            return Err(());
        }
        Ok(Self(n))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn accepts_a_digit() {
        assert_eq!("7".parse::<Level>(), Ok(Level(7)));
    }
}

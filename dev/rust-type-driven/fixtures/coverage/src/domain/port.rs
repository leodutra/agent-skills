#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Port(u16);

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Zero;

impl Port {
    // One line holds the check, the rejection and the acceptance: the rejection's own region is judged.
    pub fn new(n: u16) -> Option<Self> {
        if n == 0 { None } else { Some(Self(n)) } // expect: untested-rejection
    }
}

impl TryFrom<u16> for Port {
    type Error = Zero;

    // A None pattern matches; it does not reject.
    fn try_from(n: u16) -> Result<Self, Self::Error> {
        match Self::new(n) {
            Some(port) => Ok(port),
            None => Err(Zero), // expect: untested-rejection
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn accepts_a_port() {
        assert_eq!(Port::try_from(80), Ok(Port(80)));
    }
}

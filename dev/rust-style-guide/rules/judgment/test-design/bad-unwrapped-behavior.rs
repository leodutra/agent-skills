use std::str::FromStr;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Config {
    pub port: u16,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct InvalidConfig;

impl FromStr for Config {
    type Err = InvalidConfig;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let port = s.strip_prefix("port=").ok_or(InvalidConfig)?;
        port.trim().parse().map(|port| Self { port }).map_err(|_e: std::num::ParseIntError| InvalidConfig)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn fixture() -> Result<String, std::io::Error> {
        std::fs::read_to_string("tests/fixtures/config.txt")
    }

    #[test]
    fn parses_the_port() -> Result<(), Box<dyn std::error::Error>> {
        let text = fixture()?;
        let config: Config = text.parse().map_err(|_e: InvalidConfig| "invalid config")?;
        assert_eq!(config.port, 8080);
        Ok(())
    }
}

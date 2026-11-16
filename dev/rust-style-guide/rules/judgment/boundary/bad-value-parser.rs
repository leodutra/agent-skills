use std::num::NonZeroU16;
use std::str::FromStr;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Port(NonZeroU16);

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
#[error("invalid port: {0}")]
pub struct InvalidPort(String);

impl FromStr for Port {
    type Err = InvalidPort;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        s.parse::<NonZeroU16>().map(Self).map_err(|e| InvalidPort(e.to_string()))
    }
}

fn parse_port(raw: &str) -> Result<Port, String> {
    let n: u16 = raw.trim().parse().map_err(|e: std::num::ParseIntError| e.to_string())?;
    NonZeroU16::new(n).map(Port).ok_or_else(|| "port must be non-zero".to_owned())
}

#[derive(Debug, clap::Parser)]
pub struct Cli {
    #[arg(long, value_parser = parse_port)]
    pub port: Port,
}

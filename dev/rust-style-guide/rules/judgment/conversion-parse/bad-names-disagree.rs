use std::str::FromStr;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, clap::ValueEnum)]
pub enum Priority {
    Low,
    High,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct UnknownPriority;

/// Reads the priority column of the import file.
impl FromStr for Priority {
    type Err = UnknownPriority;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "lo" | "L" => Ok(Self::Low),
            "hi" | "H" => Ok(Self::High),
            _ => Err(UnknownPriority),
        }
    }
}

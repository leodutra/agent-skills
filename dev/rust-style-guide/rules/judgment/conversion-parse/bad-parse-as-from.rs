#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum LogLevel {
    Debug,
    Info,
    Warn,
}

impl From<&str> for LogLevel {
    fn from(text: &str) -> Self {
        match text {
            "debug" => Self::Debug,
            "warn" => Self::Warn,
            _ => Self::Info,
        }
    }
}

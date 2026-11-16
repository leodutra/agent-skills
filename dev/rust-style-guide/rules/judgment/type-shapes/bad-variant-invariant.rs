/// Which reports to include: all of them, or those between two timestamps (start before end).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Window {
    All,
    Between { start: u64, end: u64 },
}

#[must_use]
pub const fn includes(window: Window, at: u64) -> bool {
    match window {
        Window::All => true,
        Window::Between { start, end } => start <= at && at < end,
    }
}

// expect: clippy::wildcard_enum_match_arm
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Status {
    Draft,
    Sent,
    Paid,
}

#[must_use]
pub const fn bucket(status: Status) -> &'static str {
    match status {
        Status::Paid => "closed",
        _ => "open",
    }
}

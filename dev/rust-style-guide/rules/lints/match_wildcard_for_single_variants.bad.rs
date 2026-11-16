// expect: clippy::match_wildcard_for_single_variants
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Status {
    Draft,
    Sent,
    Paid,
}

#[must_use]
pub const fn label(status: Status) -> &'static str {
    match status {
        Status::Draft => "draft",
        Status::Sent => "sent",
        _ => "paid",
    }
}

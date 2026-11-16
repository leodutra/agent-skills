// keep: #[non_exhaustive] on InvoiceStatus
//! `invoice-format`: published on crates.io; other companies' code, which we never rebuild, matches
//! on its types.

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[non_exhaustive]
pub enum InvoiceStatus {
    Draft,
    Sent,
    Paid,
}

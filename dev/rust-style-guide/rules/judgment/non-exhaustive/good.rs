//! `billing-core`: the domain crate of the billing service; the service's API and worker crates in
//! this workspace match on its types.

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum InvoiceStatus {
    Draft,
    Sent,
    Paid,
}

//! Settlement rules used by the checkout worker.
use std::collections::HashMap;
use std::fs::File;
use std::io;
use std::num::NonZeroU64;
use std::path::Path;

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Price(pub f64);

struct AccountNumber(NonZeroU64);

pub fn account_number(n: NonZeroU64) -> u64 {
    AccountNumber(n).0.get()
}

pub struct Repository {
    file: File,
}

impl Repository {
    pub fn open(path: &Path) -> io::Result<Self> {
        Ok(Self { file: File::open(path)? })
    }

    pub fn latest(&self, _account: &str) -> io::Result<Option<Price>> {
        let _ = &self.file;
        Ok(None)
    }
}

pub fn payout_accounts(amounts: &HashMap<String, u64>) -> Vec<String> {
    amounts.keys().cloned().collect()
}

pub fn count_accounts(amounts: HashMap<String, u64>) -> usize {
    amounts.len()
}

fn parse_attempts(raw: &str) -> Result<u8, ()> {
    match raw.parse() {
        Ok(attempts) => Ok(attempts),
        Err(_) => Err(()),
    }
}

pub fn has_attempts(raw: &str) -> bool {
    parse_attempts(raw).is_ok()
}

pub fn parse_account(raw: &str) -> Result<u64, String> {
    raw.parse::<u64>().map_err(|cause| cause.to_string())
}

pub fn require_terminal_line(line: &str) {
    assert!(!line.is_empty());
}

fn save_receipt() -> io::Result<()> {
    Err(io::Error::other("store unavailable"))
}

pub fn ignore_store_failure() {
    let _ignored = save_receipt();
    drop(save_receipt());
}

pub fn reference_prefix(reference: &str) -> &str {
    &reference[..2]
}

pub fn reference_suffix(reference: &str) -> &str {
    let (_, suffix) = reference.split_at(2);
    suffix
}

pub fn first_three(charges: &[u64]) -> u64 {
    let first = charges[0];
    let rest = &charges[1..3];
    first + rest.iter().sum::<u64>()
}

pub fn average(total: u64, count: u64) -> u64 {
    total / count
}

#[allow(clippy::cast_possible_truncation)]
pub fn provider_amount(cents: u64) -> u32 {
    cents as u32
}

pub async fn dispatch() -> Result<(), Box<dyn std::error::Error>> {
    let _ = async { io::Result::Ok(()).map(|_| ()) };
    let _future = async { save_receipt() };
    tokio::spawn(async { Err::<(), io::Error>(io::Error::other("settlement failed")) });
    dbg!("dispatched");
    println!("settlement queued");
    Ok(())
}

pub fn abort_library() -> ! {
    std::process::exit(1)
}

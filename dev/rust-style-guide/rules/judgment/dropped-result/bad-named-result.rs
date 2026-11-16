use std::io::{self, Write};

/// Writes the receipt; the order is already paid.
pub fn print_receipt(out: &mut impl Write, total_cents: u64) {
    let _written: io::Result<()> = writeln!(out, "total: {total_cents} cents");
}

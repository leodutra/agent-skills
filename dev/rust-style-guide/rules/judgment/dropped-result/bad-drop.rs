use std::io::Write;

/// Writes the receipt; the order is already paid.
pub fn print_receipt(out: &mut impl Write, total_cents: u64) {
    drop(writeln!(out, "total: {total_cents} cents"));
}

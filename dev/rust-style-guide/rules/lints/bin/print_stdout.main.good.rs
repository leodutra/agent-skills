// A binary that prints, under a reasoned #[expect] at the printing site (lints.toml).
fn main() {
    let total: u32 = std::env::args().skip(1).filter_map(|a| a.parse::<u32>().ok()).sum();
    #[expect(clippy::print_stdout, reason = "the CLI's output")]
    {
        println!("{total}");
    }
}

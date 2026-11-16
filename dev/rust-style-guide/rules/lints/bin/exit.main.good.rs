// Allowed: process::exit in main.
fn run(args: &[String]) -> i32 {
    i32::from(args.len() > 2)
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    std::process::exit(run(&args));
}

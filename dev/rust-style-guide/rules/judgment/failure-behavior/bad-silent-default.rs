/// The port from the command line (`app <port>`), 8080 when none is given.
#[must_use]
pub fn port_from_args(args: &[String]) -> u16 {
    args.get(1).and_then(|arg| arg.parse().ok()).unwrap_or(8080)
}

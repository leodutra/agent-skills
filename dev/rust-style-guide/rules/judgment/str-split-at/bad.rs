/// "Ada Lovelace" becomes "A. Lovelace".
#[must_use]
pub fn short_name(full_name: &str) -> String {
    let (initial, rest) = full_name.split_at(1);
    match rest.split_once(' ') {
        Some((_, last)) => format!("{initial}. {last}"),
        None => full_name.to_owned(),
    }
}

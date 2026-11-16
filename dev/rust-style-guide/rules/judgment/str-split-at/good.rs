/// "Ada Lovelace" becomes "A. Lovelace".
#[must_use]
pub fn short_name(full_name: &str) -> String {
    match (full_name.chars().next(), full_name.split_once(' ')) {
        (Some(initial), Some((_, last))) => format!("{initial}. {last}"),
        _ => full_name.to_owned(),
    }
}

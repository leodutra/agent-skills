/// The `n`th word of a line the user typed, for the `word <n>` command.
#[must_use]
pub fn nth_word(line: &str, n: usize) -> String {
    let words: Vec<&str> = line.split_whitespace().collect();
    words[n].to_owned()
}

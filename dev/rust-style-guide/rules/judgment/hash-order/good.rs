use std::collections::HashMap;

/// The players who reached the bonus round, for the results page, by name.
#[must_use]
pub fn bonus_round(scores: &HashMap<String, u32>) -> Vec<String> {
    let mut names: Vec<String> =
        scores.iter().filter(|(_, score)| **score >= 90).map(|(name, _)| name.clone()).collect();
    names.sort();
    names
}

/// Whether `name` reached the bonus round: a lookup, so order doesn't matter.
#[must_use]
pub fn in_bonus_round(scores: &HashMap<String, u32>, name: &str) -> bool {
    scores.get(name).is_some_and(|score| *score >= 90)
}

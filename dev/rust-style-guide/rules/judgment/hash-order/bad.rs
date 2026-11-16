use std::collections::HashMap;

/// The players who reached the bonus round, for the results page.
#[must_use]
pub fn bonus_round(scores: &HashMap<String, u32>) -> Vec<String> {
    scores.iter().filter(|(_, score)| **score >= 90).map(|(name, _)| name.clone()).collect()
}

/// Identifies a bus stop: two records with the same position are the same stop, and the importer
/// dedupes stops by comparing them.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct StopId {
    pub latitude: f64,
    pub longitude: f64,
}

#[must_use]
pub fn dedupe(stops: &[StopId]) -> Vec<StopId> {
    let mut unique: Vec<StopId> = Vec::new();
    for stop in stops {
        if !unique.contains(stop) {
            unique.push(*stop);
        }
    }
    unique
}

struct Tally {
    passed: u32,
    failed: u32,
}

/// "3 passed, 1 failed".
#[must_use]
pub fn summary(results: &[bool]) -> String {
    let mut tally = Tally { passed: 0, failed: 0 };
    for &passed in results {
        if passed {
            tally.passed += 1;
        } else {
            tally.failed += 1;
        }
    }
    format!("{} passed, {} failed", tally.passed, tally.failed)
}

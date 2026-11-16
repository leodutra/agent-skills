//! Behavioral tests hidden from the run: only the prompt's pinned API (`load`, a Vec of rules).
use limits::load;

fn count(json: &str) -> Option<usize> {
    load(json).ok().map(|rules| rules.len())
}

#[test]
fn loads_a_valid_rule() {
    assert_eq!(count(r#"[{"route": "/api", "limit": 100, "window": 60, "burst": 20}]"#), Some(1));
}

#[test]
fn loads_an_empty_array() {
    assert_eq!(count("[]"), Some(0));
}

#[test]
fn burst_is_optional() {
    assert_eq!(count(r#"[{"route": "/api", "limit": 100, "window": 60}]"#), Some(1));
}

#[test]
fn burst_equal_to_the_limit_is_allowed() {
    assert_eq!(count(r#"[{"route": "/api", "limit": 5, "window": 60, "burst": 5}]"#), Some(1));
}

#[test]
fn burst_above_the_limit_is_rejected() {
    assert!(load(r#"[{"route": "/api", "limit": 5, "window": 60, "burst": 6}]"#).is_err());
}

#[test]
fn a_zero_limit_is_rejected() {
    assert!(load(r#"[{"route": "/api", "limit": 0, "window": 60}]"#).is_err());
}

#[test]
fn window_bounds_are_inclusive() {
    assert_eq!(count(r#"[{"route": "/a", "limit": 1, "window": 1}, {"route": "/b", "limit": 1, "window": 3600}]"#), Some(2));
    assert!(load(r#"[{"route": "/api", "limit": 1, "window": 0}]"#).is_err());
    assert!(load(r#"[{"route": "/api", "limit": 1, "window": 3601}]"#).is_err());
}

#[test]
fn route_must_start_with_a_slash() {
    assert!(load(r#"[{"route": "api", "limit": 1, "window": 60}]"#).is_err());
    assert!(load(r#"[{"route": "", "limit": 1, "window": 60}]"#).is_err());
    assert_eq!(count(r#"[{"route": "/", "limit": 1, "window": 60}]"#), Some(1));
}

#[test]
fn route_rejects_any_whitespace() {
    for route in ["/a b", "/a\\tb", "/a\\nb", "/a\u{2003}b", "/a\u{00a0}b", "/api "] {
        let json = format!(r#"[{{"route": "{route}", "limit": 1, "window": 60}}]"#);
        assert!(load(&json).is_err(), "accepted route {route:?}");
    }
}

#[test]
fn one_invalid_rule_fails_the_whole_load() {
    assert!(load(r#"[{"route": "/ok", "limit": 1, "window": 60}, {"route": "/bad", "limit": 0, "window": 60}]"#).is_err());
}

#[test]
fn malformed_values_are_rejected() {
    assert!(load(r#"[{"route": "/api", "limit": -1, "window": 60}]"#).is_err());
    assert!(load(r#"[{"route": "/api", "window": 60}]"#).is_err());
    assert!(load("not json").is_err());
}

//! API rate-limit rules, loaded from JSON.
use std::num::NonZeroU32;

use serde::Deserialize;

/// A route prefix: starts with `/` and holds no whitespace.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Deserialize)]
#[serde(try_from = "String")]
pub struct RoutePrefix(String);

#[derive(Debug, Clone, Copy, PartialEq, Eq, thiserror::Error)]
pub enum InvalidRoute {
    #[error("route prefix must start with '/'")]
    NoLeadingSlash,
    #[error("route prefix must not contain whitespace")]
    Whitespace,
}

impl RoutePrefix {
    pub fn try_new(raw: &str) -> Result<Self, InvalidRoute> {
        if !raw.starts_with('/') {
            return Err(InvalidRoute::NoLeadingSlash);
        }
        if raw.chars().any(char::is_whitespace) {
            return Err(InvalidRoute::Whitespace);
        }
        Ok(Self(raw.to_owned()))
    }

    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl TryFrom<String> for RoutePrefix {
    type Error = InvalidRoute;

    fn try_from(raw: String) -> Result<Self, Self::Error> {
        Self::try_new(&raw)
    }
}

/// A window length: 1 to 3600 seconds.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Deserialize)]
#[serde(try_from = "u32")]
pub struct WindowSecs(u32);

#[derive(Debug, Clone, Copy, PartialEq, Eq, thiserror::Error)]
#[error("window must be 1 to 3600 seconds")]
pub struct WindowOutOfRange;

impl WindowSecs {
    pub fn try_new(secs: u32) -> Result<Self, WindowOutOfRange> {
        if (1..=3600).contains(&secs) { Ok(Self(secs)) } else { Err(WindowOutOfRange) }
    }

    #[must_use]
    pub const fn get(self) -> u32 {
        self.0
    }
}

impl TryFrom<u32> for WindowSecs {
    type Error = WindowOutOfRange;

    fn try_from(secs: u32) -> Result<Self, Self::Error> {
        Self::try_new(secs)
    }
}

/// One rule: a burst, when given, never exceeds the limit.
#[derive(Debug, Clone, PartialEq, Eq, Deserialize)]
#[serde(try_from = "RawRule")]
pub struct Rule {
    route: RoutePrefix,
    limit: NonZeroU32,
    window: WindowSecs,
    burst: Option<NonZeroU32>,
}

/// The JSON shape; its `TryFrom` runs `Rule::try_new`.
#[derive(Debug, Deserialize)]
struct RawRule {
    route: RoutePrefix,
    limit: NonZeroU32,
    window: WindowSecs,
    burst: Option<NonZeroU32>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, thiserror::Error)]
#[error("burst {burst} exceeds the limit {limit}")]
pub struct BurstAboveLimit {
    pub burst: NonZeroU32,
    pub limit: NonZeroU32,
}

impl Rule {
    pub fn try_new(
        route: RoutePrefix,
        limit: NonZeroU32,
        window: WindowSecs,
        burst: Option<NonZeroU32>,
    ) -> Result<Self, BurstAboveLimit> {
        match burst {
            Some(burst) if burst > limit => Err(BurstAboveLimit { burst, limit }),
            _ => Ok(Self { route, limit, window, burst }),
        }
    }

    #[must_use]
    pub const fn route(&self) -> &RoutePrefix {
        &self.route
    }

    #[must_use]
    pub const fn limit(&self) -> NonZeroU32 {
        self.limit
    }

    #[must_use]
    pub const fn window(&self) -> WindowSecs {
        self.window
    }

    #[must_use]
    pub const fn burst(&self) -> Option<NonZeroU32> {
        self.burst
    }
}

impl TryFrom<RawRule> for Rule {
    type Error = BurstAboveLimit;

    fn try_from(raw: RawRule) -> Result<Self, Self::Error> {
        Self::try_new(raw.route, raw.limit, raw.window, raw.burst)
    }
}

/// The rules could not be read: malformed JSON or a rule that breaks its constraints.
#[derive(Debug, thiserror::Error)]
#[error("invalid rate-limit rules")]
pub struct LoadError(#[from] serde_json::Error);

pub fn load(json: &str) -> Result<Vec<Rule>, LoadError> {
    Ok(serde_json::from_str(json)?)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn n(v: u32) -> NonZeroU32 {
        NonZeroU32::new(v).unwrap()
    }

    #[test]
    fn route_needs_a_leading_slash() {
        assert_eq!(RoutePrefix::try_new("api"), Err(InvalidRoute::NoLeadingSlash));
    }

    #[test]
    fn route_rejects_whitespace() {
        assert_eq!(RoutePrefix::try_new("/api /v1"), Err(InvalidRoute::Whitespace));
    }

    #[test]
    fn window_bounds() {
        assert_eq!(WindowSecs::try_new(0), Err(WindowOutOfRange));
        assert_eq!(WindowSecs::try_new(3601), Err(WindowOutOfRange));
        assert_eq!(WindowSecs::try_new(3600).map(WindowSecs::get), Ok(3600));
    }

    #[test]
    fn burst_above_limit_is_rejected() {
        let route = RoutePrefix::try_new("/api").unwrap();
        let window = WindowSecs::try_new(60).unwrap();
        assert_eq!(
            Rule::try_new(route, n(10), window, Some(n(11))),
            Err(BurstAboveLimit { burst: n(11), limit: n(10) })
        );
    }

    #[test]
    fn loads_valid_rules() {
        let rules = load(r#"[{"route": "/api", "limit": 10, "window": 60, "burst": 5}]"#).unwrap();
        assert_eq!(rules.len(), 1);
        assert_eq!(rules[0].burst(), Some(n(5)));
    }

    #[test]
    fn load_rejects_a_zero_limit() {
        assert!(matches!(load(r#"[{"route": "/api", "limit": 0, "window": 60}]"#), Err(LoadError(_))));
    }

    #[test]
    fn load_runs_the_burst_rule() {
        let rules = r#"[{"route": "/api", "limit": 10, "window": 60, "burst": 11}]"#;
        let err = load(rules).unwrap_err();
        assert!(std::error::Error::source(&err).unwrap().to_string().contains("burst 11 exceeds the limit 10"));
    }
}

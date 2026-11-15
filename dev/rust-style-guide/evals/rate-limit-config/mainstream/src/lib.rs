//! API rate-limit rules, loaded from JSON.
use serde::Deserialize;

#[derive(Debug, Clone, PartialEq, Eq, Deserialize)]
pub struct Rule {
    pub route: String,
    pub limit: u32,
    pub window: u32,
    pub burst: Option<u32>,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ConfigError {
    #[error("invalid JSON: {0}")]
    Json(String),
    #[error("invalid route prefix: {0}")]
    Route(String),
    #[error("limit must be at least 1")]
    Limit,
    #[error("window must be between 1 and 3600 seconds")]
    Window,
    #[error("burst exceeds the limit")]
    Burst,
}

impl Rule {
    pub fn validate(&self) -> Result<(), ConfigError> {
        if !self.route.starts_with('/') || self.route.chars().any(char::is_whitespace) {
            return Err(ConfigError::Route(self.route.clone()));
        }
        if self.limit == 0 {
            return Err(ConfigError::Limit);
        }
        if !(1..=3600).contains(&self.window) {
            return Err(ConfigError::Window);
        }
        if self.burst.is_some_and(|burst| burst > self.limit) {
            return Err(ConfigError::Burst);
        }
        Ok(())
    }
}

pub fn load(json: &str) -> Result<Vec<Rule>, ConfigError> {
    let rules: Vec<Rule> = serde_json::from_str(json).map_err(|e| ConfigError::Json(e.to_string()))?;
    for rule in &rules {
        rule.validate()?;
    }
    Ok(rules)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn loads_valid_rules() {
        let rules = load(r#"[{"route": "/api", "limit": 10, "window": 60, "burst": 5}]"#).unwrap();
        assert_eq!(rules[0].burst, Some(5));
    }

    #[test]
    fn rejects_bad_route() {
        assert!(load(r#"[{"route": "api", "limit": 10, "window": 60}]"#).is_err());
    }

    #[test]
    fn rejects_zero_limit() {
        assert!(load(r#"[{"route": "/api", "limit": 0, "window": 60}]"#).is_err());
    }

    #[test]
    fn rejects_bad_window() {
        assert!(load(r#"[{"route": "/api", "limit": 10, "window": 0}]"#).is_err());
    }

    #[test]
    fn rejects_burst_above_limit() {
        assert!(load(r#"[{"route": "/api", "limit": 10, "window": 60, "burst": 11}]"#).is_err());
    }
}

#[derive(Debug, Clone, PartialEq, Eq, serde::Deserialize)]
pub struct Settings {
    pub workers: u16,
}

/// The domain's settings, from the JSON the operator wrote.
///
/// # Errors
/// The JSON error when `text` isn't valid settings.
pub fn settings(text: &str) -> Result<Settings, serde_json::Error> {
    serde_json::from_str(text)
}

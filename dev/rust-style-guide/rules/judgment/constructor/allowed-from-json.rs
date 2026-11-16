// keep: the Settings::from_json constructor
#[derive(Debug, Clone, PartialEq, Eq, serde::Deserialize)]
pub struct Settings {
    pub workers: u16,
}

#[derive(Debug, thiserror::Error)]
#[error("invalid settings")]
pub struct SettingsError(#[source] serde_json::Error);

impl Settings {
    /// Settings from their JSON form (TOML files go through another loader).
    ///
    /// # Errors
    /// [`SettingsError`] when `text` isn't JSON settings.
    pub fn from_json(text: &str) -> Result<Self, SettingsError> {
        serde_json::from_str(text).map_err(SettingsError)
    }
}

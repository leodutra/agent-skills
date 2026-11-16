#[derive(Debug, Clone, PartialEq, Eq, serde::Deserialize)]
pub struct Settings {
    pub workers: u16,
}

#[derive(Debug, thiserror::Error)]
pub enum SettingsError {
    #[error("settings are not valid json")]
    Json(#[source] serde_json::Error),
}

/// # Errors
/// [`SettingsError::Json`] when `text` isn't valid settings.
pub fn settings(text: &str) -> Result<Settings, SettingsError> {
    serde_json::from_str(text).map_err(SettingsError::Json)
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum LoginError {
    #[error("unknown user")]
    UnknownUser,
    #[error("invalid token")]
    InvalidToken,
}

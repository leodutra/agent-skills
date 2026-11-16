#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum LoginError {
    #[error("Unknown user.")]
    UnknownUser,
    #[error("invalid token {0}")]
    InvalidToken(String),
}

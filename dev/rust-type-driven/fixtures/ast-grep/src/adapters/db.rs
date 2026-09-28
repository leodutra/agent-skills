// Adapter code: outside the domain path.
impl Pool {
    pub fn connect(url: &str) -> Result<Self, DbError> { todo!() }
    pub fn new(url: &str) -> Result<Self, DbError> { todo!() }
}
#[derive(Debug, thiserror::Error)]
pub enum DbError {
    #[error("pool closed")] Closed,
    #[error("Pool is closed.")] Styled, // expect: error-message-style
}
#[derive(Debug, Default, Deserialize)]
pub struct PoolConfig(String);

pub fn a() -> Result<u8, String> { Err("bad".into()) } // expect: stringly-typed-error, stringly-typed-error
pub fn b(x: u8) -> Result<u8, OrderError> { Err(format!("bad {x}")) } // expect: stringly-typed-error
pub fn c() -> Result<u8, OrderError> { Err("bad".to_string()) } // expect: stringly-typed-error
pub fn d() -> Result<u8, OrderError> { Err(String::from("bad")) } // expect: stringly-typed-error
pub fn e() -> Result<u8, OrderError> { Err(OrderError::EmptyOrder) }
pub fn f(v: Value) -> Result<u8, OrderError> { Err(v.into()) }
pub fn g() -> Option<String> { Some("fine".into()) }

#[derive(Debug, thiserror::Error)]
pub enum LoadError {
    #[error("raw")] Raw(std::io::Error), // expect: infra-error-without-source
    #[error("kept")] Kept(#[source] std::io::Error),
    #[error("converted")] Converted(#[from] sqlx::Error),
    #[error("field")] Field { err: reqwest::Error }, // expect: infra-error-without-source
    #[error("field kept")] FieldKept { #[source] err: reqwest::Error },
    #[error("implicit")] Implicit { source: io::Error },
    #[error("not found")] NotFound { id: OrderId },
}

pub fn a() -> Result<u8, String> { Err("bad".into()) } // expect: stringly-typed-error, stringly-typed-error
pub fn b(x: u8) -> Result<u8, OrderError> { Err(format!("bad {x}")) } // expect: stringly-typed-error
pub fn c() -> Result<u8, OrderError> { Err("bad".to_string()) } // expect: stringly-typed-error
pub fn d() -> Result<u8, OrderError> { Err(String::from("bad")) } // expect: stringly-typed-error
pub fn e() -> Result<u8, OrderError> { Err(OrderError::EmptyOrder) }
pub fn f(v: Value) -> Result<u8, OrderError> { Err(v.into()) }
pub fn g() -> Option<String> { Some("fine".into()) }

// Holds causes, so it is exempt from domain-error-derives.
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

#[derive(Debug, thiserror::Error)]
pub enum OrderError { // expect: domain-error-derives
    #[error("empty order")] EmptyOrder,
}
#[derive(Debug, Clone, thiserror::Error)]
pub enum PriceError { // expect: domain-error-derives
    #[error("sale price is not below the regular price")] NotACut,
}
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum EmailError {
    #[error("Email is empty")] Capitalized, // expect: error-message-style
    #[error("email is missing '@'.")] Period, // expect: error-message-style
    #[error("HTTP request failed")] Acronym,
    #[error("I/O failed on {path}")] Slash { path: String },
    #[error("{0} is not an email")] Leading(u16),
    #[error("email is too long, e.g. {len} bytes")] Middle { len: usize },
    // ast-grep-ignore: error-message-style -- Stripe is a name
    #[error("Stripe declined the charge")] Declined,
}
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum PortError {
    #[error("port must be non-zero")] Zero,
    #[error("invalid port number: {0}")] Syntax(#[from] ParseIntError),
}

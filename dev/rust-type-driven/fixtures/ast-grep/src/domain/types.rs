// Domain types. Each line that must be flagged ends with `expect: <rule-id>`.

/// Built without its constructor.
#[derive(Debug, Clone, Deserialize)]
pub struct Email(String); // expect: domain-structural-deserialize

/// Routed through TryFrom: fine.
#[derive(Debug, Deserialize)]
#[serde(try_from = "String")]
pub struct Name(String);

/// Serialize only: fine.
#[derive(Serialize)]
pub struct Tag(String);

/// Fieldless: every value is valid, fine.
#[derive(Deserialize)]
pub enum Status { Open, Closed }

/// Carries data.
#[derive(Deserialize)]
pub enum Contact { Email(String), Phone { number: String } } // expect: domain-structural-deserialize

// Role names.
pub struct OrderManager; // expect: generic-role-name
pub trait PaymentService {} // expect: generic-role-name
pub enum StringUtils {} // expect: generic-role-name
pub type Helper = u8; // expect: generic-role-name
pub struct Order;
// OrderManager in a comment is fine
pub fn label() -> &'static str { "PaymentService in a string is fine" }
pub struct Wrapper(OrderManagerId);

// Constructor names.
impl Email {
    pub fn new(raw: String) -> Result<Self, EmailError> { todo!() } // expect: fallible-new
    pub fn parse(raw: &str) -> Result<Self, EmailError> { todo!() }
}
impl PriceCut {
    pub fn try_new(sale: Money, regular: Money) -> Result<Self, PriceError> { todo!() }
}
impl Buffer {
    pub fn new() -> Self { todo!() }
    pub fn open(path: &Path) -> io::Result<Self> { todo!() }
}
impl Port {
    pub fn new(n: u16) -> std::io::Result<Self> { todo!() } // expect: fallible-new
}
impl Ratio {
    pub fn new(n: u32) -> Option<Self> { todo!() }
}

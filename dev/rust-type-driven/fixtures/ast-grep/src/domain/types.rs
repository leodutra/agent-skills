// Domain types. Each line that must be flagged ends with `expect: <rule-id>`.

// A refinement (a private field) that a derive builds without its constructor.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Deserialize)]
pub struct Email(String); // expect: refinement-bypass
#[derive(Debug, Clone, PartialEq, Eq, Hash, Deserialize)]
#[serde(transparent)]
pub struct Handle(String); // expect: refinement-bypass
#[derive(Debug, Clone, PartialEq, Eq, Hash, sqlx::Type)]
#[sqlx(transparent)]
pub struct Sku(String); // expect: refinement-bypass
#[derive(Debug, Clone, PartialEq, Eq, Deserialize)]
pub struct Window { pub start: u32, end: u32 } // expect: refinement-bypass

/// Routed through the constructor: fine.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Deserialize)]
#[serde(try_from = "String", into = "String")]
pub struct Name(String);

/// A tag: its field is pub, so it has no invariant to skip. Fine.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Deserialize)]
#[serde(transparent)]
pub struct UserId(pub u64);

/// A record of domain types, every field pub: each field parses itself. Fine.
#[derive(Deserialize)]
pub struct OrderUpdate { pub status: Option<OrderStatus>, pub note: Option<Note> }

/// Serialize only: fine.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize)]
pub struct Label(String);

/// Enums are not refinements: a fieldless one has no invalid value, and variant fields are public
/// and parse themselves. Fine.
#[derive(Deserialize)]
pub enum Status { Open, Closed }
#[derive(Deserialize)]
pub enum Contact { Email(Email), Phone { number: PhoneNumber } }

// Default on a refinement.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Default)]
pub struct Items(Vec<Item>); // expect: refinement-default
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default)]
// ast-grep-ignore: refinement-default -- zero cents is a valid amount
pub struct Cents(i64);
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default)]
pub struct Retries(pub u8);

// Newtype derives.
#[derive(Debug, Clone, PartialEq)]
pub struct Token(String); // expect: newtype-derives
pub struct Bare(u8); // expect: newtype-derives
#[derive(Debug, Clone, Copy, PartialEq)]
// ast-grep-ignore: newtype-derives -- an f64 has neither Eq nor Hash
pub struct Ratio(f64);
#[derive(Debug, Clone, PartialEq, Eq)]
#[derive(Hash, PartialOrd, Ord)]
pub struct Rank(u8);
pub struct Pair(u8, u8);
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Lookup(BTreeMap<String, u8>);
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Wide(
    pub VeryLongTypeNameThatWrapsTheLine,
);

// Role names.
pub struct OrderManager; // expect: generic-role-name
pub trait PaymentService {} // expect: generic-role-name
pub enum StringUtils {} // expect: generic-role-name
pub type Helper = u8; // expect: generic-role-name
pub struct Order;
// OrderManager in a comment is fine
pub fn label() -> &'static str { "PaymentService in a string is fine" }
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Wrapper(OrderManagerId);

// Yes-or-no validation.
pub fn is_valid_email(raw: &str) -> bool { todo!() } // expect: validation-predicate
impl Signup {
    pub fn validate(&self) -> Result<(), SignupError> { todo!() } // expect: validation-predicate
    pub fn validate_age(&self) -> std::result::Result<(), SignupError> { todo!() } // expect: validation-predicate
    pub fn is_verified(&self) -> bool { todo!() }
    pub fn validated(self) -> Result<ValidSignup, SignupError> { todo!() }
    pub fn validate_into(self) -> Result<ValidSignup, SignupError> { todo!() }
}

// Conversions.
impl TryFrom<u8> for Level { type Error = Infallible; fn try_from(n: u8) -> Result<Self, Self::Error> { todo!() } } // expect: infallible-try-from
impl std::convert::TryFrom<u16> for Level { type Error = std::convert::Infallible; fn try_from(n: u16) -> Result<Self, Self::Error> { todo!() } } // expect: infallible-try-from
impl TryFrom<u32> for Level { type Error = LevelError; fn try_from(n: u32) -> Result<Self, Self::Error> { todo!() } }
impl From<u8> for Rank { fn from(n: u8) -> Self { todo!() } }

// Constructor names.
impl Code {
    pub fn try_new(raw: &str) -> Result<Self, CodeError> { todo!() } // expect: try-new-without-new
}
impl Slug {
    pub fn new(raw: &str) -> Option<Self> { todo!() }
    pub fn try_new(raw: &str) -> Result<Self, SlugError> { todo!() } // expect: try-new-without-new
}
impl Buffer {
    pub fn new(capacity: usize) -> Self { todo!() }
    pub fn try_new(capacity: usize) -> Result<Self, AllocError> { todo!() }
}

// Literals.
pub const HTTP: Port = Port::literal(80);
pub static HTTPS: Port = Port::literal(443);
pub fn fallback() -> Port { Port::literal(8080) } // expect: literal-outside-const
pub fn inline() -> Port { const { Port::literal(8443) } }
impl Port {
    pub const fn literal(n: u16) -> Self { todo!() }
}

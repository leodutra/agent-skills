//! One case per lint of rust_type_driven_lints. A flagged line ends with `expect: <lint>`.

pub mod domain {
    use std::fmt;
    use std::str::FromStr;

    /// A std error: the constructors below fail with it.
    #[derive(Debug)]
    pub struct Invalid;
    impl fmt::Display for Invalid {
        fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { f.write_str("invalid") }
    }
    impl std::error::Error for Invalid {}

    /// A public field on a type with a fallible constructor.
    pub struct Email {
        pub value: String, // expect: pub_field_on_invariant_type
    }
    impl Email {
        pub fn new(raw: &str) -> Result<Self, Invalid> {
            if raw.contains('@') { Ok(Self { value: raw.to_owned() }) } else { Err(Invalid) }
        }
    }

    /// A new returning Option is a fallible constructor too.
    pub struct Port(pub u16); // expect: pub_field_on_invariant_type
    impl Port {
        pub fn new(n: u16) -> Option<Self> { if n == 0 { None } else { Some(Self(n)) } }
    }

    /// TryFrom is a fallible constructor too.
    pub struct Age(pub u8); // expect: pub_field_on_invariant_type
    impl TryFrom<i64> for Age {
        type Error = Invalid;
        fn try_from(years: i64) -> Result<Self, Invalid> { u8::try_from(years).map(Age).map_err(|_| Invalid) }
    }

    /// FromStr is a fallible constructor too.
    pub struct Level {
        pub value: u8, // expect: pub_field_on_invariant_type
    }
    impl FromStr for Level {
        type Err = Invalid;
        fn from_str(raw: &str) -> Result<Self, Invalid> { raw.parse().map(|value| Level { value }).map_err(|_| Invalid) }
    }

    /// Private fields behind the constructor: fine.
    pub struct Name {
        value: String,
    }
    impl Name {
        pub fn new(raw: &str) -> Result<Self, Invalid> { if raw.is_empty() { Err(Invalid) } else { Ok(Self { value: raw.to_owned() }) } }
        pub fn as_str(&self) -> &str { &self.value }
    }

    /// A method returning Option<Self> is a transition, not a constructor: a record may keep public fields.
    pub struct Counter {
        pub count: u8,
    }
    impl Counter {
        pub fn increment(self) -> Option<Self> { self.count.checked_add(1).map(|count| Self { count }) }
    }

    /// No fallible constructor: a plain record may keep public fields.
    pub struct Point {
        pub x: i32,
        pub y: i32,
    }

    /// A refinement handing out its inner value.
    pub struct Token(String);
    impl Token {
        pub fn new(raw: &str) -> Option<Self> { if raw.is_empty() { None } else { Some(Self(raw.to_owned())) } }
        pub fn value_mut(&mut self) -> &mut String { &mut self.0 } // expect: refinement_escape
        pub fn as_str(&self) -> &str { &self.0 }
        fn trimmed(&mut self) -> &mut String { self.0.truncate(8); &mut self.0 }
        pub fn shorten(&mut self) { let _ = self.trimmed(); }
    }
    impl std::ops::Deref for Token { type Target = str; fn deref(&self) -> &str { &self.0 } } // expect: refinement_escape
    impl std::ops::DerefMut for Token { fn deref_mut(&mut self) -> &mut str { self.0.as_mut_str() } } // expect: refinement_escape
    impl AsMut<str> for Token { fn as_mut(&mut self) -> &mut str { self.0.as_mut_str() } } // expect: refinement_escape
    impl AsRef<str> for Token { fn as_ref(&self) -> &str { &self.0 } }

    /// A tag has no invariant to escape: it may deref.
    pub struct Label(pub String);
    impl std::ops::Deref for Label { type Target = str; fn deref(&self) -> &str { &self.0 } }

    /// Error types that are not std errors.
    pub struct NotAnError;
    #[derive(Debug)]
    pub struct NotSend(pub std::rc::Rc<u8>);
    impl fmt::Display for NotSend {
        fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { f.write_str("not send") }
    }
    impl std::error::Error for NotSend {}
    pub fn bare(raw: &str) -> Result<u8, ()> { raw.parse().map_err(|_| ()) } // expect: error_not_std_error
    pub fn untyped(raw: &str) -> Result<u8, NotAnError> { raw.parse().map_err(|_| NotAnError) } // expect: error_not_std_error
    pub fn not_send(raw: &str) -> Result<u8, NotSend> { raw.parse().map_err(|_| NotSend(std::rc::Rc::new(0))) } // expect: error_not_std_error
    pub struct Mode;
    impl FromStr for Mode {
        type Err = NotAnError; // expect: error_not_std_error
        fn from_str(raw: &str) -> Result<Self, NotAnError> { if raw == "on" { Ok(Mode) } else { Err(NotAnError) } }
    }
    pub fn typed(raw: &str) -> Result<u8, Invalid> { raw.parse().map_err(|_| Invalid) }
    pub fn foreign(raw: &str) -> Result<u8, std::num::ParseIntError> { raw.parse() }
    fn private_unit(raw: &str) -> Result<u8, ()> { raw.parse().map_err(|_| ()) }
    pub fn uses_private_unit() -> u8 { private_unit("1").unwrap_or(0) }

    pub struct OrderId(i64);

    pub fn find_order(order_id: i64) -> Option<u8> { let _ = order_id; None } // expect: primitive_domain_param
    pub fn rename(name: &str, email: String) { let _ = (name, email); } // expect: primitive_domain_param, primitive_domain_param
    pub fn lookup(id: uuid::Uuid) { let _ = id; } // expect: primitive_domain_param
    pub fn count(items: usize) -> usize { items }
    pub fn by_newtype(order_id: OrderId) { let _ = order_id.0; }
    fn private_helper(order_id: i64) -> i64 { order_id }
    pub fn uses_private() -> i64 { private_helper(1) }
    #[cfg_attr(dylint_lib = "rust_type_driven_lints", expect(primitive_domain_param, reason = "kept for existing callers"))]
    pub fn legacy(order_id: i64) { let _ = order_id; }
}

pub mod http {
    /// Outside domain code: the handler parses raw input, fine.
    pub fn handler(order_id: i64) { let _ = order_id; }
}

pub async fn load() -> String {
    std::fs::read_to_string("x").unwrap_or_default() // expect: blocking_in_async
}
pub async fn pause() {
    std::thread::sleep(std::time::Duration::from_millis(1)); // expect: blocking_in_async
}
pub async fn in_block() {
    let removal = async { std::fs::remove_file("x") }; // expect: blocking_in_async
    let _ = removal.await;
}
pub async fn offloaded() {
    let _ = std::thread::spawn(|| std::fs::read("x"));
}
pub fn not_async() -> std::io::Result<String> {
    std::fs::read_to_string("x")
}

trait LoadOrders { // expect: single_impl_trait
    fn load(&self) -> u8;
}
struct Db;
impl LoadOrders for Db {
    fn load(&self) -> u8 { 1 }
}
pub fn load_orders() -> u8 { Db.load() }

trait ChargePayment {
    fn charge(&self) -> u8;
}
struct Card;
impl ChargePayment for Card {
    fn charge(&self) -> u8 { 2 }
}
pub fn charge() -> u8 { Card.charge() }

pub trait Exported {
    fn value(&self) -> u8;
}
pub struct Only;
impl Exported for Only {
    fn value(&self) -> u8 { 3 }
}

#[cfg(test)]
mod tests {
    struct FakeCard;
    impl super::ChargePayment for FakeCard {
        fn charge(&self) -> u8 { 0 }
    }

    #[test]
    fn a_double_justifies_the_trait() {
        use super::ChargePayment;
        assert_eq!(FakeCard.charge(), 0);
    }
}

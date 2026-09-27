//! One case per lint of rust_type_driven_lints. A flagged line ends with `expect: <lint>`.

pub mod domain {
    /// A public field on a type with a fallible constructor.
    pub struct Email {
        pub value: String, // expect: pub_field_on_invariant_type
    }
    impl Email {
        pub fn parse(raw: &str) -> Result<Self, ()> {
            if raw.contains('@') { Ok(Self { value: raw.to_owned() }) } else { Err(()) }
        }
    }

    /// TryFrom is a fallible constructor too.
    pub struct Age(pub u8); // expect: pub_field_on_invariant_type
    impl TryFrom<i64> for Age {
        type Error = ();
        fn try_from(years: i64) -> Result<Self, ()> { u8::try_from(years).map(Age).map_err(|_| ()) }
    }

    /// Private fields behind the constructor: fine.
    pub struct Name {
        value: String,
    }
    impl Name {
        pub fn try_new(raw: &str) -> Result<Self, ()> { if raw.is_empty() { Err(()) } else { Ok(Self { value: raw.to_owned() }) } }
        pub fn as_str(&self) -> &str { &self.value }
    }

    /// No fallible constructor: a plain record may keep public fields.
    pub struct Point {
        pub x: i32,
        pub y: i32,
    }

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

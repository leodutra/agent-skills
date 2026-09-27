/// A record outside domain code: it may derive Deserialize.
#[derive(Deserialize)]
pub struct CreateOrderRequest { pub customer_id: String }

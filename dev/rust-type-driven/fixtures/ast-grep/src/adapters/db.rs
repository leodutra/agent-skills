// Adapter code: std's action names stay idiomatic for fallible constructors.
impl Pool {
    pub fn connect(url: &str) -> Result<Self, DbError> { todo!() }
    pub fn new(url: &str) -> Result<Self, DbError> { todo!() } // expect: fallible-new
}

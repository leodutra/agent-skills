// Integration tests may build string errors for their own fixtures.
fn fail() -> Result<(), String> { Err("fixture".into()) }

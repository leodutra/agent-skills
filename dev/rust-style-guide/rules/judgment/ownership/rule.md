- Borrow inputs (`&str`, `&[T]`, `&T`, `Option<&T>`); own only to store, return or consume. No clone
  to quiet the borrow checker: shorten the borrow, move the value or change the API.
- Shared ownership (`Rc`/`Arc`) only where the lifetime really is shared (state that spawned tasks
  or handlers hold), never to escape a borrow; `Weak` breaks a cycle. A handle already shared inside
  (sqlx `Pool`, reqwest `Client`) is cloned, not wrapped in another `Arc`.
- Domain code: no interior mutability (`&mut self`; the caller shares), atomics and `OnceCell`
  included. Time and randomness are parameters, never ambient, also when the source isn't listed in
  `clippy.toml`.

Question: does this code break any of these rules?

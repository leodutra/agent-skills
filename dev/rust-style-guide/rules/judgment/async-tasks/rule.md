- A trait whose futures are spawned multithreaded returns `impl Future<Output = …> + Send`.
- No blocking on the runtime (`std::fs`, sync clients, heavy CPU): async APIs or `spawn_blocking`.

Question: does this code break any of these rules?

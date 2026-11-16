- A domain or library API MUST NOT return a dependency's error raw: wrap it in a variant of your
  own, kept as `#[source]` (or `#[from]`). An infrastructure adapter whose natural contract is std's
  error (`io::Result`) MAY return it.
- `anyhow`/`eyre` only where errors only get printed (a binary's `main` and CLI commands), with
  `.context(…)`.
- Messages: lowercase, no trailing period, say what is wrong, never echo secret input.

Question: does this code break any of these rules?

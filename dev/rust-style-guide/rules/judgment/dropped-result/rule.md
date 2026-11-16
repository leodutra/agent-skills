`Result` means failure, so no error is dropped silently: handle it, or where dropping is right (a
send whose receiver may be gone) say why with `#[expect(clippy::let_underscore_must_use, reason = "…")]`.
A future MUST be awaited, returned or spawned. This covers every way of discarding one: `let _ = …`,
a binding named `_something` that is never used, `drop(…)`, `.ok();`.

Question: does this code discard a `Result` or a future without handling it and without saying why?

---
type: llm
focus: trace
weight: 1
---

review.md flags that load's `let Ok(Some(bytes)) = … else { return Ok(None) }` turns a store failure (an io::Error from get) into Ok(None), "never archived", and asks for that failure to be returned as an Err

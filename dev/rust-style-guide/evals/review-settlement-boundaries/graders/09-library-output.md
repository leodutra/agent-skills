---
type: llm
focus: trace
weight: 1
---

review.md flags `dbg!`, `println!` and `std::process::exit` in library code as defects, explaining that the library should return failures or use structured logging instead of printing or terminating the process.

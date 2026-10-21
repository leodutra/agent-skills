---
type: llm
focus: trace
weight: 1
---

Invalid transitions return a typed error enum with typed context (thiserror or a std::error::Error impl), never a String error or a panic

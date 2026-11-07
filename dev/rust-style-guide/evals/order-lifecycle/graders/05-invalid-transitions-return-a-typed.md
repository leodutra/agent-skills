---
type: llm
focus: trace
weight: 1
---

Invalid transitions return a typed error with typed context (thiserror or a std::error::Error impl; an enum, or a struct whose fields are typed states), never a String or &str context, a String error or a panic

---
type: llm
focus: trace
weight: 1
---

review.md flags the RwLock inside Stock as interior mutability in a domain type and asks for it to leave the type (for example &mut self over a plain map, sharing left to the caller); objecting only to lock poisoning, or only suggesting Mutex, does not count

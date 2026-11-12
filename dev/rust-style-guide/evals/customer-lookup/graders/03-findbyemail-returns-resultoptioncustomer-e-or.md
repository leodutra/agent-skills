---
type: llm
focus: trace
weight: 1
---

find_by_email returns Result<Option<Customer>, E> or an equivalent: a customer that does not exist is Ok(None) and a storage failure is Err, and no layer between the store and the caller turns a storage failure into None

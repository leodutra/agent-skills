---
type: llm
focus: trace
weight: 1
---

review.md flags that Sku parses text only through TryFrom<&str>/TryFrom<String> and asks for FromStr as its canonical parser; keeping those TryFrom impls as conveniences that delegate is fine

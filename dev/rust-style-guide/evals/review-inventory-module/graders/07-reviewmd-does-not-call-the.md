---
type: llm
focus: trace
weight: 1
---

No finding in review.md names the unwrap() or unwrap_err() calls inside the #[test] functions in tests/stock.rs as its problem. It fails only when those calls are themselves the defect a finding reports. It passes when review.md says they are allowed, does not mention them, or changes other code in the tests (how a Sku is built, what is asserted), even when the fix shown for that other finding uses `?` and a test returning Result

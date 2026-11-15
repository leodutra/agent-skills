---
type: llm
kind: convention
focus: trace
weight: 1
---

review.md does not call ArchiveError's missing Clone, PartialEq or Eq derives a defect, not even as a nit: its io::Error and serde_json::Error causes can't provide them

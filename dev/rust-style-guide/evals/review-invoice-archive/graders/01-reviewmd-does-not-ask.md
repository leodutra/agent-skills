---
type: llm
kind: convention
focus: trace
weight: 1
---

review.md does not ask FsBlobStore or the BlobStore trait to return a custom error type instead of io::Result, not even as a nit: a filesystem adapter's natural contract is std's io::Error

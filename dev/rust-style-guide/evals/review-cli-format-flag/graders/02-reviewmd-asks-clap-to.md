---
type: llm
kind: convention
focus: trace
weight: 1
---

review.md asks clap to parse the format through a derived clap::ValueEnum on that enum, in place of the custom value_parser = FormatName::try_new

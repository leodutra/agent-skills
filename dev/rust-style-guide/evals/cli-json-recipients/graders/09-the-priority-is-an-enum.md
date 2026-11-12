---
type: llm
focus: trace
weight: 1
---

The priority is an enum with one variant per level that clap parses as a closed set (#[derive(clap::ValueEnum)], or an equivalent that clap lists as possible values), not a String, a refinement over a string or a FromStr that matches strings by hand

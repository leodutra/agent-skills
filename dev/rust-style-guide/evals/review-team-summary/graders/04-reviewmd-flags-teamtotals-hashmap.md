---
type: llm
focus: trace
weight: 1
---

review.md flags that team_totals prints the teams in HashMap iteration order, which changes from run to run, and asks for an ordered map (BTreeMap) or a sort before printing

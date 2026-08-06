# >>> claude-context-stack >>> (condensed, managed by stack-init - edits here are overwritten)
1. Architecture/cross-module -> graphify (graphify-out/GRAPH_REPORT.md, `graphify query`/`path`). Never grep/read-many for this.
2. Specific symbols -> Serena (find_symbol, find_referencing_symbols, get_symbols_overview). Never grep for symbol names. On "No active project", call activate_project on this checkout's root, then retry - never fall back to grep.
5. Anything that executes -> Bash (RTK compresses it). Never an MCP shell tool, and on Windows never the PowerShell tool either (RTK's hook is Bash-only) except for Windows-only work.
6. Graph = last REBUILD. Uncommitted+symbol -> Serena. Uncommitted+architectural -> `graphify update .` first, then query.
Precedence on conflict: code/LSP (Serena) > graph (graphify).
# <<< claude-context-stack <<<

# >>> claude-context-stack >>> (managed by stack-init - edits here are overwritten)
## Context routing (non-negotiable)
1. Architecture / cross-module / "what connects X to Y" / blast radius:
   IF graphify-out/ exists -> read graphify-out/GRAPH_REPORT.md or run
   `graphify query "..."` / `graphify path A B`. Never orient by reading files or grep.
   IF absent -> orient normally (the stack autobuilds the graph in the background
   at session start - it may simply not be ready yet).
2. Specific symbols (definitions, references, implementations, file overviews)
   -> Serena (find_symbol, find_referencing_symbols, get_symbols_overview).
   Never grep for symbol names.
   Serena starts each session with NO ACTIVE PROJECT - writing .serena/project.yml
   configures it but does not activate it. If a Serena tool answers "No active
   project", call activate_project on this checkout's root (the SessionStart hook
   prints its path and name) and retry. Never take that error as a reason to grep.
3. Compile / type / lint state -> Serena get_diagnostics_for_file.
   Do not run a full type-check just to read diagnostics Serena already provides.
4. Edits to existing symbols -> Serena symbol-level edits (replace_symbol_body,
   insert_after_symbol, rename_symbol), not string/regex replacement.
5. Anything that executes (tests, builds, git, tooling) -> Bash. RTK compresses it.
   Do NOT route execution through an MCP shell tool or the PowerShell tool -
   RTK's hook matches Bash only, so both hand back uncompressed output.
   PowerShell is for genuinely Windows-only work (registry, COM, cmdlets).
6. The graph reflects the last REBUILD (normally the last commit).
   - Symbol-level questions about uncommitted work -> Serena (live). Never the graph.
   - ARCHITECTURAL questions that involve uncommitted work -> run `graphify update .`
     first (incremental, content-hash cached, cheap), then query the graph as normal.

## Source-of-truth precedence (on conflict)
code/LSP (Serena)  >  graph (graphify)
The LSP is live ground truth; the graph is a derivation that can trail the working
tree. On conflict, trust the LSP and rebuild the graph (`graphify update .`).
# <<< claude-context-stack <<<

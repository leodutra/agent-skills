# >>> claude-context-stack >>> (managed by stack-init - edits here are overwritten)
## Context routing (non-negotiable)
1. Serena is OPT-IN and is usually OFF. Check whether its tools are actually
   present before routing anything to it. If they are absent, that is the normal
   state - use Claude Code's native tools and do NOT ask for Serena to be
   enabled. Rules 2-4 apply only when its tools are loaded.
2. Specific symbols (definitions, references, implementations, file overviews)
   -> Serena when enabled (find_symbol, find_referencing_symbols,
   get_symbols_overview). Do not grep for symbol names when these are available.
   Serena starts each session with NO ACTIVE PROJECT - writing .serena/project.yml
   configures it but does not activate it. If a Serena tool answers "No active
   project", call activate_project on this checkout's root and retry. Never take
   that error as a reason to grep while the tools are loaded.
3. Compile / type / lint state -> Serena get_diagnostics_for_file when enabled.
   Do not run a full type-check just to read diagnostics Serena already provides.
4. Edits to existing symbols -> Serena symbol-level edits (replace_symbol_body,
   insert_after_symbol, rename_symbol) when enabled, not string/regex replacement.
5. Anything that executes (tests, builds, git, tooling) -> Bash.
   Do NOT route execution through an MCP shell tool. Nothing compresses tool
   output downstream, so prefer targeted commands over ones that dump.
   PowerShell is for genuinely Windows-only work (registry, COM, cmdlets).
6. Orientation ("what connects X to Y", blast radius, how this repo is
   organized) has no dedicated tool. Answer it by reading and searching, and
   keep that search scoped - it is the most expensive thing you do.

## Source of truth
The LSP (Serena, when enabled) is live ground truth - it reflects the working
tree right now, including uncommitted changes. Nothing in this stack derives or
caches a second model of the code, so there is no precedence conflict to resolve.
# <<< claude-context-stack <<<

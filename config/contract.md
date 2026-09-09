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
   Serena carries nine tools and nothing else: those in rules 2-4, plus
   activate_project. It has no memory, no onboarding and no file tools - do not
   look for them.
5. Anything that executes (tests, builds, git, tooling) -> Bash.
   Nothing compresses tool output downstream, so prefer targeted commands over
   ones that dump. PowerShell is for genuinely Windows-only work (registry,
   COM, cmdlets).
6. Orientation ("what connects X to Y", blast radius, how this repo is
   organized) -> codegraph_explore, in ONE call, naming the file or symbol so a
   body comes back instead of a subsystem. Its payloads are dense and stay
   resident, so ask narrow questions. Only some checkouts are indexed: on an
   unindexed path the tool answers with guidance instead of data, and that is
   the signal to fall back to reading and searching - keep that search scoped,
   it is the most expensive thing you do. Prefer the codegraph_explore TOOL over
   the `codegraph` CLI; the CLI is for subagents, and only where this repo's
   CLAUDE.local.md says the index exists.

## Source of truth

The LSP (Serena, when enabled) is live ground truth - it reflects the working
tree right now, including uncommitted changes.

codegraph is the one derived model in this stack: a pre-built index that
auto-syncs on file change but can lag an edit you just made. So it outranks
grep on "how does this fit together" and never outranks the LSP or the file on
disk on "what does this say right now". After your own edits, check its
staleness banner rather than trusting a result silently.

# <<< claude-context-stack <<<

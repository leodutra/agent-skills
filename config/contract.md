# >>> claude-context-stack >>> (managed by stack-init - edits here are overwritten)
## Context routing (non-negotiable)
1. Serena (LSP) is ON but starts idle, with no project and no language server.
   Boot it when a task first reads, searches or edits code: load its deferred
   tools in ONE ToolSearch call,
   "select:mcp__serena__activate_project,mcp__serena__find_symbol,mcp__serena__find_referencing_symbols,mcp__serena__get_symbols_overview,mcp__serena__get_diagnostics_for_file,mcp__serena__replace_symbol_body,mcp__serena__insert_after_symbol,mcp__serena__insert_before_symbol,mcp__serena__rename_symbol",
   then call activate_project with the repo root the SessionStart hook names.
   Activation starts the language server, so skip it for docs/config-only work.
   Native tools are for docs, config and plain text, or when that ToolSearch
   returns no Serena tools or Serena errors on that file's language.
   One Serena serves the whole session, subagents included, with ONE active
   project. A subagent in a different worktree than the session must not call
   activate_project or use Serena; it uses native tools. After EnterWorktree or
   ExitWorktree, call activate_project with the new checkout's root before the
   next Serena call.
2. Specific symbols (definitions, references, file overviews) -> Serena
   (find_symbol with include_body, find_referencing_symbols,
   get_symbols_overview), not grep or whole-file reads. If a tool answers "No
   active project", you skipped the boot: call activate_project on this
   checkout's root and retry; never take that error as a reason to grep.
3. Compile / type / lint state -> Serena get_diagnostics_for_file, not a full
   type-check just to read diagnostics.
4. Edits to existing symbols -> Serena symbol-level edits (replace_symbol_body,
   insert_after_symbol, insert_before_symbol, rename_symbol), not string/regex
   replacement. Serena carries these tools plus activate_project and nothing
   else: no memory, no onboarding, no file tools - do not look for them.
5. Anything that executes (tests, builds, git, tooling) -> Bash.
   Nothing compresses tool output downstream, so prefer targeted commands over
   ones that dump. PowerShell is for genuinely Windows-only work (registry,
   COM, cmdlets).
6. Orientation ("what connects X to Y", blast radius, how this repo is
   organized) -> codegraph_explore (deferred: ToolSearch
   "select:mcp__codegraph__codegraph_explore" on first use), in ONE call, naming the file or symbol so a
   body comes back instead of a subsystem. Its payloads are dense and stay
   resident, so ask narrow questions. Only some checkouts are indexed: on an
   unindexed path the tool answers with guidance instead of data, and that is
   the signal to fall back to reading and searching - keep that search scoped,
   it is the most expensive thing you do. Prefer the codegraph_explore TOOL over
   the `codegraph` CLI; the CLI is for subagents, and only where this repo's
   CLAUDE.local.md says the index exists.

## Source of truth

The LSP (Serena) is live ground truth - it reflects the working
tree right now, including uncommitted changes.

codegraph is the one derived model in this stack: a pre-built index that
auto-syncs on file change but can lag an edit you just made. So it outranks
grep on "how does this fit together" and never outranks the LSP or the file on
disk on "what does this say right now". After your own edits, check its
staleness banner rather than trusting a result silently.

# <<< claude-context-stack <<<

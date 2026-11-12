# >>> claude-context-stack >>> (condensed, managed by stack-init - edits here are overwritten)

1. Serena (LSP) is ON but idle (no project, no language server). When a task first touches code, boot it: ONE ToolSearch "select:mcp__serena__activate_project,mcp__serena__find_symbol,mcp__serena__find_referencing_symbols,mcp__serena__get_symbols_overview,mcp__serena__get_diagnostics_for_file,mcp__serena__replace_symbol_body,mcp__serena__insert_after_symbol,mcp__serena__insert_before_symbol,mcp__serena__rename_symbol", then activate_project with the repo root the SessionStart hook names (this starts the language server; skip for docs/config-only work). Native tools for docs, config, plain text, or if that returns no Serena tools or Serena errors on that language. One Serena per session, subagents included, with ONE active project: a subagent in a different worktree than the session never activates or uses Serena (native tools there); after EnterWorktree/ExitWorktree, re-run activate_project on the new root first.
2. Specific symbols -> Serena (find_symbol with include_body, find_referencing_symbols, get_symbols_overview), not grep or whole-file reads. On "No active project", call activate_project on this checkout's root, then retry.
3. Diagnostics -> Serena get_diagnostics_for_file, not a full type-check.
4. Edits to existing symbols -> Serena symbol-level edits, not regex replacement. Serena has those tools plus activate_project only: no memory, no onboarding, no file tools.
5. Anything that executes -> Bash. Nothing compresses tool output downstream, so prefer targeted commands over ones that dump.
6. Orientation -> codegraph_explore (deferred: ToolSearch it on first use) in ONE call, naming the file or symbol. Dense payloads stay resident, so ask narrow. Not every checkout is indexed: unindexed paths answer with guidance, which is the signal to read and search instead, scoped.
Source of truth: the LSP (Serena) is live. codegraph is a derived index - it beats grep on structure, never beats the LSP or the file on disk on current content; check its staleness banner after your own edits.

# <<< claude-context-stack <<<

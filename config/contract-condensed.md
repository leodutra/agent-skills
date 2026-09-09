# >>> claude-context-stack >>> (condensed, managed by stack-init - edits here are overwritten)

1. Serena is OPT-IN and usually OFF. Check its tools are present before routing to it; if absent that is normal - use native tools, don't ask for it to be enabled. Rules 2-4 apply only when loaded.
2. Specific symbols -> Serena when enabled (find_symbol, find_referencing_symbols, get_symbols_overview); don't grep for symbol names while those are loaded. On "No active project", call activate_project on this checkout's root, then retry.
3. Diagnostics -> Serena get_diagnostics_for_file when enabled, not a full type-check.
4. Edits to existing symbols -> Serena symbol-level edits when enabled, not regex replacement. Serena carries nine tools only (rules 2-4 plus activate_project): no memory, no onboarding, no file tools.
5. Anything that executes -> Bash. Nothing compresses tool output downstream, so prefer targeted commands over ones that dump.
6. Orientation -> codegraph_explore in ONE call, naming the file or symbol. Dense payloads stay resident, so ask narrow. Not every checkout is indexed: unindexed paths answer with guidance, which is the signal to read and search instead, scoped.
Source of truth: the LSP when enabled is live. codegraph is a derived index - it beats grep on structure, never beats the LSP or the file on disk on current content; check its staleness banner after your own edits.

# <<< claude-context-stack <<<

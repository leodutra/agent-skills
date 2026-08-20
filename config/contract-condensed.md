# >>> claude-context-stack >>> (condensed, managed by stack-init - edits here are overwritten)
1. Serena is OPT-IN and usually OFF. Check its tools are present before routing to it; if absent that is normal - use native tools, don't ask for it to be enabled. Rules 2-4 apply only when loaded.
2. Specific symbols -> Serena when enabled (find_symbol, find_referencing_symbols, get_symbols_overview); don't grep for symbol names while those are loaded. On "No active project", call activate_project on this checkout's root, then retry.
3. Diagnostics -> Serena get_diagnostics_for_file when enabled, not a full type-check.
4. Edits to existing symbols -> Serena symbol-level edits when enabled, not regex replacement.
5. Anything that executes -> Bash. Nothing compresses tool output downstream, so prefer targeted commands over ones that dump.
6. Orientation has no dedicated tool - read and search, and keep it scoped.
Source of truth: the LSP when enabled; nothing here caches a second model of the code.
# <<< claude-context-stack <<<

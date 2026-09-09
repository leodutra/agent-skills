# >>> claude-context-stack: codegraph >>> (managed by stack-init - edits here are overwritten)
## CodeGraph is indexed for this checkout

`.codegraph/` exists here, so the `codegraph` CLI answers orientation questions
(contract rule 6) without a read-and-search sweep. The MCP tool
`codegraph_explore` covers the main agent; this block exists for SUBAGENTS and
for Bash, which never see the MCP server's own guidance.

- `codegraph explore "<question>"` - relevant symbols' verbatim source grouped
  by file, the call paths between them, and a blast-radius summary. One call.
- `codegraph node <symbol|file>` - one symbol's source plus its callers, or a
  line-numbered file read.
- `codegraph impact <symbol>` - what a change to that symbol reaches.
- `codegraph callers <symbol>` / `codegraph callees <symbol>`.

Treat what it returns as already read - do not re-grep to confirm it. The index
auto-syncs on file change; check the staleness banner after an edit rather than
re-indexing by hand.

Its payloads are dense and verbatim. Name the file or the symbol in the query so
one body comes back instead of a whole subsystem, and prefer a fresh session per
feature over riding one all day - the tool-call saving is real, but what it
returns stays resident and pulls compaction closer.

This block is written per checkout, never globally: `codegraph explore` on a
path with no `.codegraph/` fails and costs a turn.
# <<< claude-context-stack: codegraph <<<

# Claude Code Context Stack — Setup & Specification

> **Version:** 2.0
> **Status:** Active
> **Scope:** Three tools that reduce the token cost of working in a real codebase with Claude Code — **graphify** (structure), **Serena** (symbols), **RTK** (output compression) — plus the global routing contract that makes Claude use each for the one thing it's best at. No intent/docs layer. Targets Arch Linux and Windows; Rust/TypeScript/Python.
> **Canonical executables:** `stack-setup.sh` (Linux/macOS) and `stack-setup.ps1` (Windows). They are self-documenting and self-installing. This document is the spec-of-whys; the scripts are the source of truth for behavior. Change behavior in the scripts; record reasoning here.
> **Changelog:** 2.0 — removed the docs/intent layer (SPEC/ADR/worklog) and per-project skill; consolidated install into a single self-documenting installer per OS (`stack-setup`); dropped `graphify claude install` (see §8); Serena now registered at user scope. 1.x — five-layer model with docs layer and `stack-init` bootstrap.
> **Audience:** Both the human installing it and the agent operating inside it. Sections marked `[AGENT]` are mirrored into the global routing contract.

---

## 1. Purpose and design principle

Claude Code's effectiveness on a real codebase is bounded by context quality, not model intelligence. Context degrades from three uncontrolled sources of waste, and each tool eliminates exactly one:

| Waste source | What it looks like | Owned by |
|---|---|---|
| **Orientation** | Re-reading dozens of files to learn what connects to what | graphify |
| **Retrieval & editing** | Whole-file dumps, grep walls, regex edits that miss aliased refs | Serena |
| **Tool-output noise** | Thousands of tokens of passing-test boilerplate per `cargo test` | RTK |

Two design principles:

**One question per layer; no layer answers another layer's question.** Most failure modes are *layer bleed* — the agent BFS-ing the graph for a symbol lookup, grepping for a symbol name, or running tests through an MCP shell that bypasses RTK. The configuration makes boundaries structural where possible (e.g. Serena's shell tool is simply not exposed) and instructional (the routing contract) where not.

**Sources have tiers of truth.** The LSP is ground truth by construction — it is the compiler's live model. The graph is a deterministic but potentially stale *derivation* of committed code. When they disagree, the LSP wins and the graph is rebuilt (§5). This matters more once retrieval is cheap, not less: the cheaper a wrong answer is to obtain, the more explicitly its trust level must be marked.

What this stack deliberately does **not** do: manage intent (specs, ADRs, roadmaps) or conventions. Those are valuable but they are not context *compression* — they are content, and earlier versions that scaffolded them added a maintenance surface that drifted. The stack is now only the three tools that move tokens, plus the contract.

---

## 2. Component roles and hard boundaries

### 2.1 graphify — the map (structure)

**Answers:** "What connects X to Y?", "What's the blast radius of touching Z?", "How is this codebase organized?", "Where do I start looking?"

**Mechanism:** tree-sitter parses code locally (zero API calls) into a typed graph of files/functions/classes/tables with contain/import/invoke edges, persisted as `graphify-out/graph.json` plus a human/agent-readable `GRAPH_REPORT.md` (god nodes, communities, surprising connections). A content-hash cache makes rebuilds incremental.

**Why it's in the stack:** it converts the most expensive operation in agentic coding — cold orientation on a large repo — into a one-time build plus cheap queries. Value is front-loaded: first sessions, unfamiliar areas, cross-module tracing, refactor-impact analysis.

**Hard boundary:** graphify is NOT for targeted symbol lookup. A graph BFS can return ~1,500 tokens for a query Serena answers in a fraction of that. If the question names a specific symbol, it is not a graphify question.

**Staleness model:** the graph is a build-time snapshot, kept fresh by a git post-commit hook (installed per repo by `stack-setup init`). It is correct as of the **last commit** — never for uncommitted work-in-progress. The agent must know this: **the graph trails the working tree.**

### 2.2 Serena — the eyes and hands (symbols)

**Answers:** "Where is symbol S defined?", "Who references S?", "What's in this file?", "Does this file have errors?", and performs symbol-precise edits.

**Mechanism:** an MCP server wrapping real language servers (rust-analyzer, typescript-language-server, pyright) over LSP. No precomputed index of its own — it queries the live language server, so answers reflect the working tree *right now*, including uncommitted changes. Confirmed tools include `find_symbol`, `find_referencing_symbols`, `get_symbols_overview`, `get_diagnostics_for_file` / `get_diagnostics_for_symbol`, and symbol-level edits (`replace_symbol_body`, `insert_after_symbol`, `insert_before_symbol`).

**Why it's in the stack:** it is the only layer that provides ground truth. `find_referencing_symbols` returns actual call sites, not text matches — no false positives from comments, strings, or look-alike methods. `get_diagnostics_for_file` returns structured compile/type/lint state without running (or paying for) a full `cargo check` dump.

**Hard boundaries (enforced by the `ide-assistant` context):**

1. `execute_shell_command` is **disabled** by default in `ide-assistant` — keep it that way. MCP tool calls bypass RTK's Bash hook; if tests ran through Serena you'd pay full uncompressed output cost. All shell goes through Claude Code's native Bash.
2. `read_file` / `search_for_pattern` are likewise disabled in `ide-assistant` — Claude Code provides those natively, and duplicate tools confuse routing.

These are structural, not instructional: the tools simply aren't in Serena's surface, so the agent *can't* route around RTK.

### 2.3 RTK — the filter (output compression)

**Answers:** nothing. RTK is invisible plumbing. A PreToolUse hook (matcher: `Bash`) rewrites supported commands to their `rtk` equivalent before execution, and the model receives 60–90% fewer tokens of output. Failures, errors, diffs, and stack traces are preserved in full; compression targets boilerplate and pass-noise. `cargo test` compresses ~92%, `git status` ~81%.

**Why it's in the stack:** test/build/git/tooling output is the single largest uncontrolled token sink in a session. Over a session this is the difference between one context window and three.

**Two usage modes:**

- **Output mode (automatic, primary):** the PreToolUse hook. Zero workflow change.
- **Input mode (manual):** call filters directly and capture stdout when assembling context on purpose — `rtk ls src/`, `rtk git log -n 20`, `rtk read path`, `rtk grep pattern`. Useful for session-start summaries or feeding compressed state to subagents. (A first-class "inject into prompt at position X" mode is an unshipped upstream feature request; manual capture is the supported path.)

**Hard boundary:** RTK compresses output of ~100 known dev commands. It is not a semantic/prose compressor — it will not shrink markdown or arbitrary text. Don't ask it to.

---

## 3. `[AGENT]` Routing matrix

Route every information need to exactly one layer.

| Question shape | Route to | NOT to | Why |
|---|---|---|---|
| "How is this organized / what's the architecture?" | graphify (`GRAPH_REPORT.md`, `graphify query`) | reading files, grep | Orientation is precomputed; orienting by file-reading burns 10–50× the tokens |
| "What connects A to B?" / "between these modules?" | graphify (`graphify path A B`) | grep, Serena | Multi-hop relationships are graph traversals; the LSP sees one hop at a time |
| "Blast radius if I change X?" (module level) | graphify first, then Serena to confirm exact refs | grep | Graph gives community-level spread; LSP confirms precise call sites |
| "Where is symbol S defined / who calls S?" | Serena (`find_symbol`, `find_referencing_symbols`) | graphify, grep | LSP is exact and current; the graph may be stale, grep has false positives |
| "What implements / uses this trait or type?" | Serena (`find_referencing_symbols`) | grep | Only the LSP resolves this correctly |
| "What's in this file?" (structure, not content) | Serena (`get_symbols_overview`) | reading the whole file | An overview costs a fraction of a full read |
| "Does this compile / what are the type errors?" | Serena (`get_diagnostics_for_file`) | running `cargo check` via Bash | Diagnostics are structured and already minimal; no compression heuristics involved |
| Editing a function/class body | Serena (`replace_symbol_body`, `insert_*_symbol`) | regex/string replace | Symbol-anchored edits don't hit comments, strings, or look-alike names |
| Renaming / refactoring a symbol | Serena symbol-level edits | search-and-replace | Avoids missed aliased imports and false hits |
| Running tests / builds / linters / git / docker | Bash (RTK compresses automatically) | any MCP shell tool | The RTK hook only covers Bash; an MCP shell would bypass it |
| Fuzzy "where's the code that handles ~concept~?" | graphify query first; Serena once a symbol name surfaces | reading many files | Graph narrows the neighborhood; LSP takes over at symbol granularity |

**Tie-breakers:**

- Question names a **specific symbol** → Serena, always.
- Question spans **more than one module** or asks about *shape* → graphify first.
- Question is about **uncommitted work-in-progress** → Serena (live), never graphify (graph trails the working tree).
- Anything that **executes** → Bash.

---

## 4. The routing contract `[AGENT]`

This is the text the global installer writes into `~/.claude/CLAUDE.md` (between sentinel markers, so re-running replaces it cleanly and touches nothing else). `stack-setup contract` prints it. It is the authoritative, always-on instruction — there is no per-project copy.

```markdown
## Context routing (non-negotiable)
1. Architecture / cross-module / "what connects X to Y" / blast radius:
   IF graphify-out/ exists -> read graphify-out/GRAPH_REPORT.md or run
   `graphify query "..."` / `graphify path A B`. Never orient by reading files or grep.
   IF absent -> orient normally, and suggest running the stack init in this repo.
2. Specific symbols (definitions, references, implementations, file overviews)
   -> Serena (find_symbol, find_referencing_symbols, get_symbols_overview).
   Never grep for symbol names.
3. Compile / type / lint state -> Serena get_diagnostics_for_file.
   Do not run a full type-check just to read diagnostics Serena already provides.
4. Edits to existing symbols -> Serena symbol-level edits (replace_symbol_body,
   insert_after_symbol), not string/regex replacement.
5. Anything that executes (tests, builds, git, tooling) -> Bash. RTK compresses it.
   Do NOT route execution through any MCP shell tool - that bypasses RTK.
6. The graph reflects the LAST COMMIT. For uncommitted work, use Serena (live).

## Source-of-truth precedence (on conflict)
code/LSP (Serena)  >  graph (graphify)
The LSP is live ground truth; the graph is a derivation that can trail the working
tree. On conflict, trust the LSP and rebuild the graph (`graphify update .`).
```

Rule 1 is **conditional** because the contract is global: it applies even in repos where `stack-setup init` never ran. Without the guard, the agent would be ordered to consult a graph that doesn't exist; with it, un-initialized repos degrade gracefully and the agent nudges toward init.

---

## 5. `[AGENT]` Precedence and divergence — the epistemic spec

Two sources can disagree. Tiered by how they acquire truth:

| Tier | Source | Epistemic status | Staleness |
|---|---|---|---|
| 1 | Serena / LSP | Ground truth — the compiler's live model | Never (live working tree) |
| 2 | graphify graph | Deterministic derivation of committed code | Trails the working tree by ≤1 commit (post-commit hook) |

**Rules:**

1. Tier 2 vs tier 1 conflict → the graph is stale; trust the LSP and rebuild (`graphify update .`).
2. For uncommitted work, the graph is silent or wrong by definition — use Serena.
3. The graph is for *shape* (what connects to what); the LSP is for *fact* (what a symbol is and where it's used). A graph edge is a hypothesis about a relationship; confirm specifics at tier 1 before acting on them.

**Why precedence is explicit:** compression and cheap retrieval make every source easier to trust, including the stale one. Marking the trust order is the mitigation.

---

## 6. Installation and operating model

Everything in the stack is either *configuration* (how tools behave — global by nature) or *state* (a derivation of one codebase — per-repo by nature). The split:

| | Global (once, ever) | Per-repo (`stack-setup init`) |
|---|---|---|
| RTK | hook in `~/.claude/settings.json` (`rtk init -g`) | — |
| Serena | MCP registration at **user scope** | onboarding memories (auto, first session) |
| graphify | `uv tool install graphifyy[all]`, `graphify install` | `graphify .`, post-commit hook, `graphify-out/` |
| Routing contract | `~/.claude/CLAUDE.md` (§4) | — |
| Language servers | rust-analyzer / ts-ls / pyright — once per language | — |

The graph and its refresh hook are the only irreducibly per-repo pieces: there is no graph until a repo exists, and `.git/hooks` is per-repo by construction. Everything else is set once.

### 6.1 Global install — `stack-setup` (no args)

Run once. The installer:

1. **RTK** — `cargo install` if absent, then `rtk init -g` (global Bash PreToolUse hook).
2. **Serena** — `claude mcp add --scope user serena -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context ide-assistant`. **No `--project` flag** — registered bare, Serena activates the project from the session's cwd, so one registration serves every repo. `--context ide-assistant` is what disables the shell/read/search tools (§2.2).
3. **graphify** — `uv tool install 'graphifyy[all]'` (PyPI package is `graphifyy`, double-y; `uv tool`/`pipx` over plain `pip` because PATH issues are the most common "command not found" cause), then `graphify install` for the `/graphify` skill. It deliberately does **not** run `graphify claude install` — see §8.
4. **Routing contract** — writes §4 into `~/.claude/CLAUDE.md` between sentinel markers (idempotent).

Prereqs: `git`, `claude` (required); `cargo`, `uv`, `pip` (for the installs); a language server per language.

### 6.2 Per-repo init — `stack-setup init`

Run once from each repo root (idempotent). Builds the graph (`graphify .`), installs the post-commit incremental-rebuild hook (`graphify hook install`), and gitignores `graphify-out/`. Writes nothing to any CLAUDE.md — the global contract covers it. A repo where this never ran still works (rule 1 is conditional).

### 6.3 Other subcommands

`stack-setup verify` checks the wiring (RTK on PATH and hook active, Serena registered, graphify installed, contract present, and — in a repo — graph built and hook landed). `stack-setup contract` prints the routing contract for inspection.

### 6.4 Windows

`stack-setup.ps1` is the Windows installer — same `global` / `init` / `verify` / `contract` modes, step-for-step parity, equally idempotent. Use PowerShell, not `cmd`: the contract write needs here-strings; batch would force `^`-escaping of every `|`/`>`/`<`/`&`. If a `cmd.exe` entry point is required, wrap it (`@powershell -ExecutionPolicy Bypass -File "%~dp0stack-setup.ps1" %*`).

| Concept | Unix | Windows (PowerShell) |
|---|---|---|
| Claude config dir | `~/.claude/` | `$env:USERPROFILE\.claude\` |
| Routing contract | `~/.claude/CLAUDE.md` | `$env:USERPROFILE\.claude\CLAUDE.md` |
| Run the installer | `stack-setup` | `.\stack-setup.ps1` |

Notes: `graphify hook install` writes a shell post-commit hook that runs via **Git for Windows'** bundled bash (a prerequisite). First run may need `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. Use `graphify .`, never `/graphify .` — the leading slash is a path separator in PowerShell.

### 6.5 Optional — graphify MCP query server

For graph queries as MCP tools instead of CLI calls, add a `graphify` server to `.mcp.json`. The CLI (`graphify query`, `graphify path` via Bash) is the leaner default — its output flows through RTK and it adds zero always-loaded tool definitions. Add the MCP server only if the agent under-uses the graph.

---

## 7. Guardrails and known failure modes

**Layer bleed (most common).** Agent greps for a symbol, or graph-walks for a definition. Mitigation: the routing contract (§4). Note that graphify's own grep-redirect hook is *not* installed in this setup and is a no-op on current Claude Code anyway (§8) — the contract is the mechanism, not a hook.

**Stale graph trusted as current.** Graph reflects the last commit; agent reasons about mid-refactor code from it. Mitigation: precedence rule (§5) + the post-commit hook bounding lag to one commit; `graphify update . --force` after branch switches or large refactors.

**Over-compression eating a needed signal.** An RTK filter strips context the agent needed. Mitigation: RTK preserves failures in full and dumps raw output to disk on failure; run `rtk discover` periodically; verify the broken-test path once at setup. Don't pass secrets as CLI args — RTK's tracking DB stores full command strings for ~90 days.

**Shell routing around RTK.** Any MCP tool that executes commands bypasses the Bash hook. Mitigation: structural — `ide-assistant` exposes no Serena shell tool. If you add another MCP server with an exec tool, decide its compression story explicitly.

**Hook integrity.** The only PreToolUse hook now is RTK's (`Bash`). If another tool's installer rewrites the hook array instead of merging, RTK's could be clobbered. After installing anything that touches `settings.json`, confirm the `Bash` → rtk hook is still present (`stack-setup verify`).

---

## 8. Decisions log (the whys, condensed)

**Docs/intent layer removed (vs 1.x).** The stack is only the three token-reducing tools. Specs/ADRs/worklogs are content, not compression; scaffolding them added a maintenance surface that drifted and a precedence tangle. Out of scope here.

**`graphify claude install` dropped.** It would write a second, near-duplicate "read GRAPH_REPORT.md" directive into the same global `CLAUDE.md` as the routing contract, and its Glob/Grep PreToolUse hook is a no-op on Claude Code builds after the late-May-2026 tool-architecture change. Rule 1 of the contract is the authoritative, always-on instruction; `graphify install` (the skill) is still wired so `/graphify` and the CLI work.

**Serena at user scope, no `--project`.** One registration serves every repo, activating from the session's cwd. Per-repo memories stay in each repo's `.serena/`, so there's no cross-project contamination; the only cost is first-session onboarding per repo.

**Serena in `ide-assistant` context, shell disabled.** Makes the RTK-bypass impossible structurally rather than by instruction, and removes duplicate read/search tools that confuse routing.

**graphify rebuild on git post-commit, not on agent hooks.** Matches the graph's epistemic status ("true as of last commit"), avoids rebuild thrash, keeps staleness bounded and *known* rather than variable.

**graphify via CLI through Bash by default, MCP optional.** CLI output flows through RTK and costs zero standing tool definitions; the MCP server adds value only if the agent under-uses the graph.

**Diagnostics from Serena, not compressed `cargo check`.** Structured LSP data is already minimal with no lossy heuristic; compression belongs where output is noisy, not where it's already signal.

**`uv tool install` over plain `pip` for graphify.** `uv` is already required for Serena, and plain `pip` is the most common cause of `graphify: command not found` (PATH).

**RTK input mode = manual `$(rtk ...)` capture.** The first-class prompt-injection mode is an unshipped upstream proposal; manual capture is the supported equivalent and keeps placement under your control.

**Single self-documenting installer per OS.** The doc is the spec-of-whys; `stack-setup.sh` / `stack-setup.ps1` are the executables and the source of truth for behavior. One fact, one home: change behavior in the script, record reasoning here.

---

## 9. Setup verification checklist

```bash
# Global
rtk gain                                   # non-zero after a few Bash commands -> hook live
claude mcp list | grep -i serena           # registered, no --project arg
grep -q "Context routing" ~/.claude/CLAUDE.md   # contract present
command -v graphify                        # installed and on PATH

# Per repo (after `stack-setup init`)
ls -l graphify-out/graph.json              # graph built
git commit --allow-empty -m test && ls -l graphify-out/graph.json  # mtime advanced -> hook fires

# Behavior, in a Claude session
#  - architecture question  -> reads GRAPH_REPORT.md / runs graphify, does NOT grep
#  - "who calls <fn>"        -> find_referencing_symbols, does NOT grep
#  - get_diagnostics_for_file on a planted type error -> structured error, no file dump
#  - agent tool list shows NO serena execute_shell_command / read_file
#  - one-time: break a test on purpose -> failure detail survives RTK compression
#  - repo WITHOUT graphify-out/ -> agent orients normally and suggests init (no error)
```

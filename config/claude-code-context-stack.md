# Claude Code Context Stack — Setup & Specification

> **Version:** 2.1.1
> **Status:** Active
> **Scope:** Four tools that reduce the token cost of working in a real codebase with Claude Code — **graphify** (structure), **Serena** (symbols), **RTK** (output compression), **Headroom** (proxy-layer compression) — plus the global routing contract that makes Claude route the first three to the one thing each is best at. Headroom needs no routing decision; see §2.4. No intent/docs layer. Targets Arch Linux and Windows; Rust/TypeScript/Python.
> **Canonical executables:** `stack-init.sh` (Linux/macOS) and `stack-init.ps1` (Windows). They are self-documenting and self-installing. This document is the spec-of-whys; the scripts are the source of truth for behavior. Change behavior in the scripts; record reasoning here.
> **Changelog:** 2.1.1 — installer name unified to `stack-init` everywhere (docs previously said `stack-setup` while the shipped files were already `stack-init.*`); no behavior change. 2.1 — added Headroom as a fourth, proxy-layer tool (§2.4); sessions must launch via `headroom wrap claude` for it to engage (see §6.1, §7). 2.0 — removed the docs/intent layer (SPEC/ADR/worklog) and per-project skill; consolidated install into a single self-documenting installer per OS (then called `stack-setup`); dropped `graphify claude install` (see §8); Serena now registered at user scope. 1.x — five-layer model with docs layer and a `stack-init` bootstrap (name coincidence with the current installer; different tool).
> **Audience:** Both the human installing it and the agent operating inside it. Sections marked `[AGENT]` are mirrored into the global routing contract.

---

## 1. Purpose and design principle

Claude Code's effectiveness on a real codebase is bounded by context quality, not model intelligence. Context degrades from four uncontrolled sources of waste, and each tool eliminates exactly one:

| Waste source | What it looks like | Owned by |
|---|---|---|
| **Orientation** | Re-reading dozens of files to learn what connects to what | graphify |
| **Retrieval & editing** | Whole-file dumps, grep walls, regex edits that miss aliased refs | Serena |
| **Tool-output noise** | Thousands of tokens of passing-test boilerplate per `cargo test` | RTK |
| **Wire-level residue** | Whatever still reaches the API after the three layers above act — `Read`-tool file dumps, growing conversation history | Headroom |

Three design principles:

**One question per layer; no layer answers another layer's question.** Most failure modes are *layer bleed* — the agent BFS-ing the graph for a symbol lookup, grepping for a symbol name, or running tests through an MCP shell that bypasses RTK. The configuration makes boundaries structural where possible (e.g. Serena's shell tool is simply not exposed) and instructional (the routing contract) where not. graphify and Serena chain rather than bleed on compound questions: for blast radius or fuzzy "where's the code for X" asks, graphify narrows a multi-module question to a neighborhood first, then Serena confirms the exact symbol or reference within it (§3) — two questions in sequence, each still answered by exactly the layer that owns it.

**Sources have tiers of truth.** The LSP is ground truth by construction — it is the compiler's live model. The graph is a deterministic but potentially stale *derivation* of committed code. When they disagree, the LSP wins and the graph is rebuilt (§5). This matters more once retrieval is cheap, not less: the cheaper a wrong answer is to obtain, the more explicitly its trust level must be marked.

**Compression layers compose, they don't compete.** graphify, Serena, and RTK each *eliminate* a waste source at its origin — there's nothing left for a later layer to compress. Headroom sits one level further out, at the proxy boundary, and squeezes whatever the first three didn't already remove (§2.4). It is additive on top of RTK's output, not a second attempt at RTK's job: compressing already-compressed Bash output again is harmless and small, never required.

What this stack deliberately does **not** do: manage intent (specs, ADRs, roadmaps) or conventions. Those are valuable but they are not context *compression* — they are content, and earlier versions that scaffolded them added a maintenance surface that drifted. The stack is now only the four tools that move tokens, plus the contract.

---

## 2. Component roles and hard boundaries

### 2.1 graphify — the map (structure)

**Answers:** "What connects X to Y?", "What's the blast radius of touching Z?", "How is this codebase organized?", "Where do I start looking?"

**Mechanism:** tree-sitter parses code locally (zero API calls) into a typed graph of files/functions/classes/tables with contain/import/invoke edges, persisted as `graphify-out/graph.json` plus a human/agent-readable `GRAPH_REPORT.md` (god nodes, communities, surprising connections). A content-hash cache makes rebuilds incremental.

**Why it's in the stack:** it converts the most expensive operation in agentic coding — cold orientation on a large repo — into a one-time build plus cheap queries. Value is front-loaded: first sessions, unfamiliar areas, cross-module tracing, refactor-impact analysis.

**Hard boundary:** graphify is NOT for targeted symbol lookup. A graph BFS can return ~1,500 tokens for a query Serena answers in a fraction of that. If the question names a specific symbol, it is not a graphify question.

**Staleness model:** the graph is a build-time snapshot, kept fresh by a git post-commit hook (installed per repo by `stack-init init`). It is correct as of the **last commit** — never for uncommitted work-in-progress. The agent must know this: **the graph trails the working tree.**

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

### 2.4 Headroom — the safety net (wire-level compression)

**Answers:** nothing, like RTK. Headroom is the last thing that touches a request before it leaves the machine.

**Mechanism:** [chopratejas/headroom](https://github.com/chopratejas/headroom) (PyPI: `headroom-ai`) runs as a local proxy. Launching a session with `headroom wrap claude` starts the proxy, points Claude Code's API traffic at it (`ANTHROPIC_BASE_URL`), and recompresses whatever is in the outgoing request — reversibly, so full content is retrievable on demand. Unlike RTK's PreToolUse hook (fires per Bash command, before the result ever enters context), Headroom sits at the wire, after everything else has already shaped the context.

**Why it's in the stack:** the other three layers eliminate waste at its source, but two things still reach the API uncompressed by design: `Read`-tool file dumps (Serena's own `read_file` is structurally disabled, §2.2, so file content comes through Claude Code's native tool instead) and the conversation history itself, which only grows over a session. Headroom is the one layer positioned to catch both.

**Hard boundaries:**

1. Only engages for sessions launched via `headroom wrap claude`. A bare `claude` invocation skips the proxy entirely — RTK, Serena, and graphify are unaffected (they wire into the session, not the launch command), but Headroom contributes nothing. `stack-init verify` can confirm the binary is installed; it cannot detect how the current session was launched (§7).
2. `--code-graph` is deliberately never passed. It would have Headroom build its own structure graph, duplicating graphify and creating two disagreeing sources for the same question — exactly the layer bleed §1 exists to prevent.
3. `--memory` is deliberately never passed. This stack manages no intent/memory layer by design (§1); that flag's scope is out of bounds here regardless of what it does upstream.
4. Compression is additive on RTK's output, never a substitute for it — RTK runs first and is free to skip (it only rewrites ~100 known commands); Headroom runs second and compresses whatever's left, known commands or not.

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

Headroom doesn't appear in this matrix because it never routes a question — like RTK, it is invisible plumbing, not a layer the agent chooses to query. The only thing it requires of the human, not the agent, is launching the session correctly (§2.4, §7).

---

## 4. The routing contract `[AGENT]`

This is the text the global installer writes into `~/.claude/CLAUDE.md` (between sentinel markers, so re-running replaces it cleanly and touches nothing else). `stack-init contract` prints it. It is the authoritative, always-on instruction — there is no per-project copy.

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

Rule 1 is **conditional** because the contract is global: it applies even in repos where `stack-init init` never ran. Without the guard, the agent would be ordered to consult a graph that doesn't exist; with it, un-initialized repos degrade gracefully and the agent nudges toward init.

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

Most of the stack is either *configuration* (how tools behave — global by nature) or *state* (a derivation of one codebase — per-repo by nature). The split (Headroom's one exception is noted below the table):

| | Global (once, ever) | Per-repo (`stack-init init`) |
|---|---|---|
| RTK | hook in `~/.claude/settings.json` (`rtk init -g`) | — |
| Serena | MCP registration at **user scope** | onboarding memories (auto, first session) |
| graphify | `uv tool install graphifyy[all]`, `graphify install` | `graphify .`, post-commit hook, `graphify-out/` |
| Headroom | `uv tool install headroom-ai[all]` | — |
| Routing contract | `~/.claude/CLAUDE.md` (§4) | — |
| Language servers | rust-analyzer / ts-ls / pyright — once per language | — |

The graph and its refresh hook are the only irreducibly per-repo pieces: there is no graph until a repo exists, and `.git/hooks` is per-repo by construction. Everything else in this table is set once. Headroom is the exception to "once": the *install* is global-once like the rest, but *activation* is a third axis — neither global nor per-repo — decided fresh at every session launch (`headroom wrap claude` vs bare `claude`, §2.4, §7).

### 6.1 Global install — `stack-init` (no args)

Run once. The installer:

1. **RTK** — `cargo install` if absent, then `rtk init -g` (global Bash PreToolUse hook).
2. **Serena** — `claude mcp add --scope user serena -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context ide-assistant`. **No `--project` flag** — registered bare, Serena activates the project from the session's cwd, so one registration serves every repo. `--context ide-assistant` is what disables the shell/read/search tools (§2.2).
3. **graphify** — `uv tool install 'graphifyy[all]'` (PyPI package is `graphifyy`, double-y; `uv tool`/`pipx` over plain `pip` because PATH issues are the most common "command not found" cause), then `graphify install` for the `/graphify` skill. It deliberately does **not** run `graphify claude install` — see §8.
4. **Headroom** — `uv tool install 'headroom-ai[all]'` (PyPI package is `headroom-ai`; same `uv tool` preference and reasoning as graphify). Installing it is necessary but not sufficient: it only takes effect for sessions launched with `headroom wrap claude` (§2.4, §7) — the installer prints this as a reminder but cannot enforce it.
5. **Routing contract** — writes §4 into `~/.claude/CLAUDE.md` between sentinel markers (idempotent).

Prereqs: `git`, `claude` (required); `cargo`, `uv`, `pip` (for the installs); a language server per language.

### 6.2 Per-repo init — `stack-init init`

Run once from each repo root (idempotent). Builds the graph (`graphify .`), installs the post-commit incremental-rebuild hook (`graphify hook install`), and gitignores `graphify-out/`. Writes nothing to any CLAUDE.md — the global contract covers it. A repo where this never ran still works (rule 1 is conditional).

### 6.3 Other subcommands

`stack-init verify` checks the wiring (RTK on PATH and hook active, Serena registered, graphify installed, Headroom installed, contract present, and — in a repo — graph built and hook landed). It cannot check that a given session was actually launched with `headroom wrap claude` — that's a per-launch choice, not an install-time state. `stack-init contract` prints the routing contract for inspection.

### 6.4 Windows

`stack-init.ps1` is the Windows installer — same `global` / `init` / `verify` / `contract` modes, step-for-step parity, equally idempotent. Use PowerShell, not `cmd`: the contract write needs here-strings; batch would force `^`-escaping of every `|`/`>`/`<`/`&`. If a `cmd.exe` entry point is required, wrap it (`@powershell -ExecutionPolicy Bypass -File "%~dp0stack-init.ps1" %*`).

| Concept | Unix | Windows (PowerShell) |
|---|---|---|
| Claude config dir | `~/.claude/` | `$env:USERPROFILE\.claude\` |
| Routing contract | `~/.claude/CLAUDE.md` | `$env:USERPROFILE\.claude\CLAUDE.md` |
| Run the installer | `stack-init` | `.\stack-init.ps1` |

Notes: `graphify hook install` writes a shell post-commit hook that runs via **Git for Windows'** bundled bash (a prerequisite). First run may need `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. Use `graphify .`, never `/graphify .` — the leading slash is a path separator in PowerShell.

### 6.5 Optional — graphify MCP query server

For graph queries as MCP tools instead of CLI calls, add a `graphify` server to `.mcp.json`. The CLI (`graphify query`, `graphify path` via Bash) is the leaner default — its output flows through RTK and it adds zero always-loaded tool definitions. Add the MCP server only if the agent under-uses the graph.

---

## 7. Guardrails and known failure modes

**Layer bleed (most common).** Agent greps for a symbol, or graph-walks for a definition. Mitigation: the routing contract (§4). Note that graphify's own grep-redirect hook is *not* installed in this setup and is a no-op on current Claude Code anyway (§8) — the contract is the mechanism, not a hook.

**Stale graph trusted as current.** Graph reflects the last commit; agent reasons about mid-refactor code from it. Mitigation: precedence rule (§5) + the post-commit hook bounding lag to one commit; `graphify update . --force` after branch switches or large refactors.

**Over-compression eating a needed signal.** An RTK filter strips context the agent needed. Mitigation: RTK preserves failures in full and dumps raw output to disk on failure; run `rtk discover` periodically; verify the broken-test path once at setup. Don't pass secrets as CLI args — RTK's tracking DB stores full command strings for ~90 days.

**Shell routing around RTK.** Any MCP tool that executes commands bypasses the Bash hook. Mitigation: structural — `ide-assistant` exposes no Serena shell tool. If you add another MCP server with an exec tool, decide its compression story explicitly.

**Hook integrity.** The only PreToolUse hook now is RTK's (`Bash`). If another tool's installer rewrites the hook array instead of merging, RTK's could be clobbered. After installing anything that touches `settings.json`, confirm the `Bash` → rtk hook is still present (`stack-init verify`).

**Headroom silently inert.** Installed but the session was launched with a bare `claude`, not `headroom wrap claude` — everything still works, just without the wire-level compression, and nothing errors to say so. Mitigation: it's a launch-habit problem, not a config one; `stack-init verify` confirms the binary exists but can't confirm how *this* session started.

---

## 8. Decisions log (the whys, condensed)

**Docs/intent layer removed (vs 1.x).** The stack is only the four token-reducing tools. Specs/ADRs/worklogs are content, not compression; scaffolding them added a maintenance surface that drifted and a precedence tangle. Out of scope here.

**Headroom added as a fourth, proxy-layer tool (2.1).** graphify/Serena/RTK each eliminate a waste source at its origin; nothing in the original three was positioned to catch `Read`-tool file dumps or the conversation history's own growth, both of which still reach the API uncompressed. Headroom's proxy sits exactly there. See §2.4.

**Headroom's `--code-graph` and `--memory` flags never passed.** `--code-graph` would have Headroom build a second structure graph, directly duplicating graphify and reopening the layer-bleed problem §1 exists to close. `--memory` is an intent/memory feature, and this stack manages no intent layer by design (§1) — adding one back in through a flag would undo that decision by a side door.

**No automatic shell alias for `claude` → `headroom wrap claude`.** The installer prints the reminder instead of writing a shell function/profile entry for it. Two reasons: editing a user's shell profile is a persistent, easy-to-miss change to their environment that this installer otherwise avoids (it only ever touches `CLAUDE.md` and `settings.json`, both Claude-owned files); and a function literally named `claude` risks recursing into itself depending on how `headroom wrap` resolves the real binary on a given shell — untested across every shell this stack targets, so it's left as an opt-in step for the human, not a default the installer commits them to.

**`graphify claude install` dropped.** It would write a second, near-duplicate "read GRAPH_REPORT.md" directive into the same global `CLAUDE.md` as the routing contract, and its Glob/Grep PreToolUse hook is a no-op on Claude Code builds after the late-May-2026 tool-architecture change. Rule 1 of the contract is the authoritative, always-on instruction; `graphify install` (the skill) is still wired so `/graphify` and the CLI work.

**Serena at user scope, no `--project`.** One registration serves every repo, activating from the session's cwd. Per-repo memories stay in each repo's `.serena/`, so there's no cross-project contamination; the only cost is first-session onboarding per repo.

**Serena in `ide-assistant` context, shell disabled.** Makes the RTK-bypass impossible structurally rather than by instruction, and removes duplicate read/search tools that confuse routing.

**graphify rebuild on git post-commit, not on agent hooks.** Matches the graph's epistemic status ("true as of last commit"), avoids rebuild thrash, keeps staleness bounded and *known* rather than variable.

**graphify via CLI through Bash by default, MCP optional.** CLI output flows through RTK and costs zero standing tool definitions; the MCP server adds value only if the agent under-uses the graph.

**Diagnostics from Serena, not compressed `cargo check`.** Structured LSP data is already minimal with no lossy heuristic; compression belongs where output is noisy, not where it's already signal.

**`uv tool install` over plain `pip` for graphify.** `uv` is already required for Serena, and plain `pip` is the most common cause of `graphify: command not found` (PATH).

**RTK input mode = manual `$(rtk ...)` capture.** The first-class prompt-injection mode is an unshipped upstream proposal; manual capture is the supported equivalent and keeps placement under your control.

**Single self-documenting installer per OS.** The doc is the spec-of-whys; `stack-init.sh` / `stack-init.ps1` are the executables and the source of truth for behavior. One fact, one home: change behavior in the script, record reasoning here.

---

## 9. Setup verification checklist

```bash
# Global
rtk gain                                   # non-zero after a few Bash commands -> hook live
claude mcp list | grep -i serena           # registered, no --project arg
grep -q "Context routing" ~/.claude/CLAUDE.md   # contract present
command -v graphify                        # installed and on PATH
command -v headroom                        # installed and on PATH

# Per repo (after `stack-init init`)
ls -l graphify-out/graph.json              # graph built
git commit --allow-empty -m test && ls -l graphify-out/graph.json  # mtime advanced -> hook fires

# Behavior, in a Claude session
#  - architecture question  -> reads GRAPH_REPORT.md / runs graphify, does NOT grep
#  - "who calls <fn>"        -> find_referencing_symbols, does NOT grep
#  - get_diagnostics_for_file on a planted type error -> structured error, no file dump
#  - agent tool list shows NO serena execute_shell_command / read_file
#  - one-time: break a test on purpose -> failure detail survives RTK compression
#  - repo WITHOUT graphify-out/ -> agent orients normally and suggests init (no error)
#  - session started with `headroom wrap claude` -> headroom stats/logs show traffic
#    compressed; a bare `claude` session shows none (expected - confirms §7's
#    "silently inert" failure mode rather than a broken install)
```

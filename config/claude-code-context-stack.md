# Claude Code Context Stack — Setup & Specification

> **Version:** 2.3
> **Status:** Active
> **Scope:** Four tools that reduce the token cost of working in a real codebase with Claude Code — **graphify** (structure), **Serena** (symbols), **RTK** (output compression), **Headroom** (proxy-layer compression) — plus the global routing contract that makes Claude route the first three to the one thing each is best at. Headroom needs no routing decision; see §2.4. No intent/docs layer. Targets Arch Linux and Windows; Rust/TypeScript/Python.
> **Canonical executables:** `stack-init.sh` (Linux/macOS) and `stack-init.ps1` (Windows). They are self-documenting and self-installing. This document is the spec-of-whys; the scripts are the source of truth for behavior. Change behavior in the scripts; record reasoning here.
> **Changelog:** 2.3 — the two remaining manual steps automated. Per-repo init: `stack-init global` now registers a `SessionStart` graph-autobuild hook that builds a missing graph in the background on a repo's first session and incrementally refreshes an existing one at every session start; all its side effects stay under `.git/` (refresh hooks, `info/exclude` instead of `.gitignore`, build lock) so it never mutates tracked files — `stack-init init` remains as the eager variant and for the tracked-file extras (C11, §6.2). Headroom activation: bare `claude` is now shadowed by a recursion-safe shim in `~/.claude/stack-bin` — since `headroom wrap` only accepts tool names and re-resolves `claude` on PATH itself, the shim exports a re-entry guard (`CLAUDE_STACK_SHIM`) that bounds any bounce back onto the shim to exactly one hop (the re-entered shim execs the real binary, resolved by skipping its own directory); it never double-wraps an already-proxied session and falls through to the real binary on any failure; `CLAUDE_NO_HEADROOM=1` bypasses per launch; the 2.2 wrapper (`clw`/`hclaude`/`claudew`) is removed as superseded — the installer deletes any it previously wrote, and `headroom wrap claude` itself is the manual fallback; the shim passes `--no-tokensave` when the installed headroom supports it, keeping the no-second-code-graph decision enforced against upstream's default-on tokensave graph (C12, §6.1 step 4, §8). Contract rule 1's absent-branch now says the graph may be mid-autobuild instead of suggesting a manual init. 2.2 — corrected the graph's staleness model to "last rebuild" rather than "last commit" and widened rule 6 to allow an on-demand refresh for uncommitted architectural questions (C1–C2); added `post-checkout`/`post-merge`/`post-rewrite` refresh hooks alongside `post-commit`, bounding staleness to one working-tree-moving git operation and explicitly documenting worktree support (C3, C7); added a Headroom launcher wrapper (`clw`/`hclaude`/`claudew`) plus a `SessionStart` hook that detects and flags an unwrapped session (C4–C5); the routing contract now propagates a condensed form into `~/.claude/agents/` and `.claude/agents/` (`stack-init contract --condensed`) so Task-tool subagents don't layer-bleed (C6); documented a cache-economics benchmark procedure for Headroom, since wire-level compression can bust Anthropic's prompt cache even while shrinking wire tokens (C8); added `stack-init stats` for dated rtk/headroom usage snapshots (C9). Serena tool-surface auditing (C10) is deferred, gated on real usage data. 2.1.1 — installer name unified to `stack-init` everywhere (docs previously said `stack-setup` while the shipped files were already `stack-init.*`); no behavior change. 2.1 — added Headroom as a fourth, proxy-layer tool (§2.4); sessions must launch via `headroom wrap claude` for it to engage (see §6.1, §7). 2.0 — removed the docs/intent layer (SPEC/ADR/worklog) and per-project skill; consolidated install into a single self-documenting installer per OS (then called `stack-setup`); dropped `graphify claude install` (see §8); Serena now registered at user scope. 1.x — five-layer model with docs layer and a `stack-init` bootstrap (name coincidence with the current installer; different tool).
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

**Staleness model:** the graph is a build-time snapshot, kept fresh by git hooks (installed by the graph-autobuild hook or `stack-init init`; §6.2). It is correct as of the **last rebuild** (normally the last commit, because the rebuild hook fires post-commit) — never for uncommitted work-in-progress that hasn't triggered a rebuild. The agent must know this: **the graph trails the working tree.**

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

1. Only engages when the session is launched through the proxy. Since 2.3 the claude shim (§6.1 step 4) makes that the default: any launch that resolves `claude` on PATH gets wrapped. A launch that dodges the shim — the binary invoked by absolute path, `CLAUDE_NO_HEADROOM=1`, or a shell that hasn't picked up the shim's PATH entry yet — skips the proxy entirely; RTK, Serena, and graphify are unaffected (they wire into the session, not the launch command), but Headroom contributes nothing. `stack-init verify` checks the shim wins PATH resolution; the SessionStart headroom-check flags an unwrapped live session (§7).
2. `--code-graph` is deliberately never passed. It would have Headroom build its own structure graph, duplicating graphify and creating two disagreeing sources for the same question — exactly the layer bleed §1 exists to prevent.
3. `--memory` is deliberately never passed. This stack manages no intent/memory layer by design (§1); that flag's scope is out of bounds here regardless of what it does upstream.
4. Compression is additive on RTK's output, never a substitute for it — RTK runs first and is free to skip (it only rewrites ~100 known commands); Headroom runs second and compresses whatever's left, known commands or not.
5. Headroom's place in the stack is conditional, not assumed: it's retained only as long as the cache-economics benchmark (§9) shows it's net-positive on effective cost, not just on wire tokens (§7 "Compression that busts the prompt cache").

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
- Question is about **uncommitted work-in-progress**: symbol-level → Serena (live), never graphify. Architectural → run `graphify update .` first (cheap, incremental), then query the graph as normal.
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
   IF absent -> orient normally (the stack autobuilds the graph in the background
   at session start - it may simply not be ready yet).
2. Specific symbols (definitions, references, implementations, file overviews)
   -> Serena (find_symbol, find_referencing_symbols, get_symbols_overview).
   Never grep for symbol names.
3. Compile / type / lint state -> Serena get_diagnostics_for_file.
   Do not run a full type-check just to read diagnostics Serena already provides.
4. Edits to existing symbols -> Serena symbol-level edits (replace_symbol_body,
   insert_after_symbol), not string/regex replacement.
5. Anything that executes (tests, builds, git, tooling) -> Bash. RTK compresses it.
   Do NOT route execution through any MCP shell tool - that bypasses RTK.
6. The graph reflects the last REBUILD (normally the last commit).
   - Symbol-level questions about uncommitted work -> Serena (live). Never the graph.
   - ARCHITECTURAL questions that involve uncommitted work -> run `graphify update .`
     first (incremental, content-hash cached, cheap), then query the graph as normal.

## Source-of-truth precedence (on conflict)
code/LSP (Serena)  >  graph (graphify)
The LSP is live ground truth; the graph is a derivation that can trail the working
tree. On conflict, trust the LSP and rebuild the graph (`graphify update .`).
```

Rule 1 is **conditional** because the contract is global and a graph may not exist *yet*: since 2.3 the graph-autobuild hook (§6.2) builds it in the background on a repo's first session, so the absent-branch is normally a transient state rather than a missing install step. Without the guard, the agent would be ordered to consult a graph that doesn't exist; with it, graph-less repos degrade gracefully while the build lands.

---

## 5. `[AGENT]` Precedence and divergence — the epistemic spec

Two sources can disagree. Tiered by how they acquire truth:

| Tier | Source | Epistemic status | Staleness |
|---|---|---|---|
| 1 | Serena / LSP | Ground truth — the compiler's live model | Never (live working tree) |
| 2 | graphify graph | Deterministic derivation of the working tree as of the last rebuild | Trails the working tree by rebuild lag (bounded by hooks, §6.2) |

**Rules:**

1. Tier 2 vs tier 1 conflict → the graph is stale; trust the LSP and rebuild (`graphify update .`).
2. For uncommitted work, the graph is silent or wrong by definition — use Serena.
3. The graph is for *shape* (what connects to what); the LSP is for *fact* (what a symbol is and where it's used). A graph edge is a hypothesis about a relationship; confirm specifics at tier 1 before acting on them.

**Why precedence is explicit:** compression and cheap retrieval make every source easier to trust, including the stale one. Marking the trust order is the mitigation.

**Staleness bound:** one working-tree-moving git operation (commit, checkout, merge, or rebase) — each has its own refresh hook (§6.2), so the graph is never more than one such operation behind.

---

## 6. Installation and operating model

Most of the stack is either *configuration* (how tools behave — global by nature) or *state* (a derivation of one codebase — per-repo by nature). The split (Headroom's one exception is noted below the table):

| | Global (once, ever) | Per-repo (autobuilt; `stack-init init` = eager) |
|---|---|---|
| RTK | hook in `~/.claude/settings.json` (`rtk init -g`) | — |
| Serena | MCP registration at **user scope** | onboarding memories (auto, first session) |
| graphify | `uv tool install graphifyy[all]`, `graphify install`, graph-autobuild SessionStart hook | `graphify .`, refresh hooks, `graphify-out/` — all autobuilt on first session |
| Headroom | `uv tool install headroom-ai[all]` + claude shim | — |
| Routing contract | `~/.claude/CLAUDE.md` (§4) | — |
| Language servers | rust-analyzer / ts-ls / pyright — once per language | — |

The graph and its refresh hooks are the only irreducibly per-repo *state*: there is no graph until a repo exists, and `.git/hooks` is per-repo by construction. Since 2.3 that state no longer costs a per-repo *step* — the global SessionStart autobuild hook creates and maintains it (§6.2). Headroom's activation axis (per-launch, §2.4) is likewise defaulted now: the claude shim wraps every launch that resolves `claude` on PATH, and only an explicit bypass (`CLAUDE_NO_HEADROOM=1`, an absolute-path invocation, or a shell that hasn't loaded the shim's PATH entry) skips it.

### 6.1 Global install — `stack-init` (no args)

Run once. The installer:

1. **RTK** — `cargo install` if absent, then `rtk init -g` (global Bash PreToolUse hook).
2. **Serena** — `claude mcp add --scope user serena -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context ide-assistant`. **No `--project` flag** — registered bare, Serena activates the project from the session's cwd, so one registration serves every repo. `--context ide-assistant` is what disables the shell/read/search tools (§2.2).
3. **graphify** — `uv tool install 'graphifyy[all]'` (PyPI package is `graphifyy`, double-y; `uv tool`/`pipx` over plain `pip` because PATH issues are the most common "command not found" cause), then `graphify install` for the `/graphify` skill, then registers the **graph-autobuild SessionStart hook** (§6.2) that makes per-repo init automatic. It deliberately does **not** run `graphify claude install` — see §8.
4. **Headroom** — `uv tool install 'headroom-ai[all]'` (PyPI package is `headroom-ai`; same `uv tool` preference and reasoning as graphify). Installing it is necessary but not sufficient: it only takes effect for sessions launched through the proxy. Since 2.3 the installer shadows bare `claude` with a **recursion-safe shim** in `~/.claude/stack-bin`, prepended to PATH (on Unix via a marker-guarded line in `.profile`/`.bashrc`/`.zshrc`; on Windows via the user PATH in the registry, with three shim files covering PowerShell/cmd/Git-Bash resolution). `headroom wrap` only accepts tool names (click subcommands) and re-resolves `claude` on PATH itself, so re-resolution back onto the shim is unavoidable — the shim bounds it by construction: it exports a re-entry guard (`CLAUDE_STACK_SHIM`) before delegating to `headroom wrap claude`, and the re-entered shim execs the real binary directly (resolved by the shim itself, skipping its own directory) — exactly one bounce, never a loop. It never double-wraps an already-proxied session (localhost `ANTHROPIC_BASE_URL`) and falls through to exec-ing the real binary when headroom is missing or `CLAUDE_NO_HEADROOM=1` is set — a broken shim never blocks a session. The shim also passes `--no-tokensave` when the installed headroom supports it (probed at install time), because newer headroom builds its own "tokensave" code graph by default — the renamed, default-on incarnation of `--code-graph`, which §2.4 boundary 2 and §8 forbid as a duplicate of graphify. The 2.2 wrapper (`clw`/`hclaude`/`claudew`) is removed as superseded — the installer deletes any it previously wrote; where the shim's PATH entry doesn't win, `headroom wrap claude` itself is the manual fallback (§7).
5. **Routing contract** — writes §4 into `~/.claude/CLAUDE.md` between sentinel markers (idempotent).

Prereqs: `git`, `claude` (required); `cargo`, `uv`, `pip` (for the installs); a language server per language.

### 6.2 Per-repo graph — autobuilt at session start (or `stack-init init`, eager)

Since 2.3 this is automatic. A global `SessionStart` hook (`~/.claude/hooks/graph-autobuild.sh` / `.ps1`, registered by `stack-init global`) runs at every session start inside a git repo: graph present → `graphify update .` in the background (incremental, content-hash cached, silent); graph absent → it takes a build lock (`.git/claude-stack-autobuild.lock`, mkdir-atomic, treated as stale after 60 minutes), starts `graphify .` plus the four refresh hooks below in the background, adds `graphify-out/` to `.git/info/exclude`, and injects a one-line session note that a build is underway. **Everything it writes stays under `.git/`** — a background job must never mutate tracked files, which is why it uses `info/exclude` rather than `.gitignore` and skips the `.claude/agents/` contract injection. Worktree-aware: the lock lives in the worktree-private git dir (`--git-dir`), hooks and exclude in the shared one (`--git-common-dir`). Opt-outs: `CLAUDE_STACK_NO_AUTOBUILD=1` (global) or a `.graphify-skip` file in the repo root (per repo).

`stack-init init` remains as the eager variant — same graph and hooks, built in the foreground so it's ready immediately, plus the two tracked-file extras autobuild deliberately won't do: gitignoring `graphify-out/` in the repo's `.gitignore` (shareable with the team) and injecting the condensed contract into `.claude/agents/` (§6.x). Those belong in explicit, reviewable changes. A repo where neither ran still works (rule 1 is conditional).

**The four refresh hooks:** `post-commit` (`graphify hook install`, incremental rebuild) was the only one in 2.1.1. 2.2 adds three more, because any working-tree-moving git operation besides a commit left the graph stale with no bound: `post-checkout` (only on branch switches — `$3 = 1`, not per-file checkouts — backgrounded so switching isn't blocked), `post-merge`, and `post-rewrite` (fires once at the end of a rebase). All three are written merge-not-clobber: if the hook file already exists without the stack's marker comment, the refresh line is appended rather than the file being overwritten.

**Worktrees:** deliberately supported, not forbidden. Git hooks execute with cwd at the root of whichever worktree triggered them, so the triggering worktree always self-refreshes correctly — no absolute paths are baked into any hook body. Sibling worktrees catch up via `post-checkout` on their next branch switch, and via rule 6's uncommitted-architectural-question refresh (§4) if queried before that. Residual risk: a long-lived sibling worktree that never switches branches and is never asked an architectural question can sit stale indefinitely — accepted, because nothing is querying it in that state.

### 6.3 Other subcommands

`stack-init verify` checks the wiring (RTK on PATH and hook active, Serena registered, graphify installed, graph-autobuild hook registered, Headroom installed, claude shim first on PATH, contract present, and — in a repo — graph built and hooks landed). It cannot check that a given session was actually launched wrapped — that's a per-launch choice, not an install-time state; the `SessionStart` headroom-check hook (§7) covers that gap at runtime instead. `stack-init contract` prints the routing contract for inspection; `stack-init contract --condensed` prints the short form injected into subagent files (§6.x). `stack-init stats` appends a dated usage snapshot for comparing stack versions (§9).

### 6.4 Windows

`stack-init.ps1` is the Windows installer — same `global` / `init` / `verify` / `contract` modes, step-for-step parity, equally idempotent. Use PowerShell, not `cmd`: the contract write needs here-strings; batch would force `^`-escaping of every `|`/`>`/`<`/`&`. If a `cmd.exe` entry point is required, wrap it (`@powershell -ExecutionPolicy Bypass -File "%~dp0stack-init.ps1" %*`).

| Concept | Unix | Windows (PowerShell) |
|---|---|---|
| Claude config dir | `~/.claude/` | `$env:USERPROFILE\.claude\` |
| Routing contract | `~/.claude/CLAUDE.md` | `$env:USERPROFILE\.claude\CLAUDE.md` |
| Run the installer | `stack-init` | `.\stack-init.ps1` |

Notes: `graphify hook install` writes a shell post-commit hook that runs via **Git for Windows'** bundled bash (a prerequisite). First run may need `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. Use `graphify .`, never `/graphify .` — the leading slash is a path separator in PowerShell.

### 6.x Subagents

Task-tool subagents get a fresh context that does not load `~/.claude/CLAUDE.md`. RTK's `Bash` PreToolUse hook is settings-level and applies to every session including subagents' — it propagates automatically. Headroom's env (`ANTHROPIC_BASE_URL`) is inherited by child processes — it propagates automatically too. The routing contract is neither: it's prose injected into one specific file, so subagents never see it unless something puts it there.

Mitigation: `stack-init global`/`init` inject a condensed ~6-line form of the contract (rules 1, 2, 5, 6 plus the precedence line) into every `*.md` file under `~/.claude/agents/` and `.claude/agents/` respectively, between the same kind of sentinel markers used for `CLAUDE.md` (idempotent — re-running replaces the block, doesn't duplicate it). If neither directory has any agent files, the installer says so and does nothing. `stack-init contract --condensed` prints the same text for pasting into ad-hoc orchestrator prompts that spawn Task-tool subagents outside of a predefined agent file.

### 6.5 Optional — graphify MCP query server

For graph queries as MCP tools instead of CLI calls, add a `graphify` server to `.mcp.json`. The CLI (`graphify query`, `graphify path` via Bash) is the leaner default — its output flows through RTK and it adds zero always-loaded tool definitions. Add the MCP server only if the agent under-uses the graph.

---

## 7. Guardrails and known failure modes

**Layer bleed (most common).** Agent greps for a symbol, or graph-walks for a definition. Mitigation: the routing contract (§4). Note that graphify's own grep-redirect hook is *not* installed in this setup and is a no-op on current Claude Code anyway (§8) — the contract is the mechanism, not a hook.

**Stale graph trusted as current.** Graph reflects the last rebuild; agent reasons about mid-refactor code from it. Mitigation: precedence rule (§5) + the four refresh hooks (§6.2) bounding lag to one working-tree-moving git operation, plus rule 6's on-demand refresh before uncommitted architectural questions. `graphify update . --force` is now a fallback for anomalies (e.g. a hook failed to fire), not the primary mitigation.

**Over-compression eating a needed signal.** An RTK filter strips context the agent needed. Mitigation: RTK preserves failures in full and dumps raw output to disk on failure; run `rtk discover` periodically; verify the broken-test path once at setup. Don't pass secrets as CLI args — RTK's tracking DB stores full command strings for ~90 days.

**Shell routing around RTK.** Any MCP tool that executes commands bypasses the Bash hook. Mitigation: structural — `ide-assistant` exposes no Serena shell tool. If you add another MCP server with an exec tool, decide its compression story explicitly.

**Hook integrity.** The only PreToolUse hook now is RTK's (`Bash`). If another tool's installer rewrites the hook array instead of merging, RTK's could be clobbered. After installing anything that touches `settings.json`, confirm the `Bash` → rtk hook is still present (`stack-init verify`).

**Headroom silently inert.** Installed but the session launched unwrapped — everything still works, just without the wire-level compression. 2.2 added a habit-sized wrapper (`clw`) and detection via a `SessionStart` hook (`~/.claude/hooks/headroom-check.sh`/`.ps1`) that checks whether `ANTHROPIC_BASE_URL` points at a local proxy and, if not, injects a one-line `NOTE: Headroom proxy not active this session...` into context. 2.3 makes prevention the default: the claude shim (§6.1 step 4) wraps bare `claude` automatically, so the NOTE now effectively means "the shim was bypassed" — a shell that hasn't loaded the shim's PATH entry, an absolute-path launch, a launcher that spawns the binary without a PATH search (some IDE integrations), or an explicit `CLAUDE_NO_HEADROOM=1`. `stack-init verify` checks the shim wins PATH resolution at install time; the SessionStart hook is what catches a live unwrapped session.

**Subagent layer bleed.** Task-tool subagents get fresh contexts that don't include `~/.claude/CLAUDE.md` — RTK's hook and Headroom's env both inherit automatically (they're settings-level / process-level), but the routing contract does not, so spawned agents can grep for symbols or orient by file-reading exactly where token volume is highest. Mitigation (§6.x "Subagents"): `stack-init global`/`init` inject a condensed ~8-line form of the contract into every file under `~/.claude/agents/` and `.claude/agents/`; orchestrator prompts for ad-hoc Task calls should paste `stack-init contract --condensed` into the subagent prompt.

**Compression that busts the prompt cache.** Headroom's wire-level rewriting is, by default, a prefix-cache invalidator: recompressing history changes the bytes the API sees turn to turn. Symptom: `headroom stats` shows savings while `cache_read_input_tokens` (from `/cost` or OTEL metrics) collapses relative to a bare session — fewer wire tokens can still mean *more* money once cache misses are priced in. A known contributor is CCR injecting a `headroom_retrieve` tool definition; changing the tool list between turns busts Anthropic's entire prefix cache regardless of what else changed. Mitigation: confirm Headroom's CacheAligner is active; check the upstream CCR/tool-injection issue status; escape hatch is running bare — RTK, Serena, and graphify are completely unaffected, since Headroom is the only optional-per-launch layer (§2.4). See §9 for the benchmark that decides whether Headroom is net-positive for a given usage pattern.

---

## 8. Decisions log (the whys, condensed)

**Uncommitted architectural questions get a refresh, not a blanket ban (2.2).** 2.1.1's rule 6 forbade the graph outright for any uncommitted work, on the assumption that the graph is inherently commit-bound. C1 corrected that assumption: the graph is bound to the *last rebuild*, and `graphify update .` is an incremental, content-hash-cached, cheap operation — so an architectural question mid-refactor can legitimately trigger a refresh-then-query instead of falling back to file-reading. Symbol-level questions about uncommitted work still route to Serena, never the graph. Rejected alternative: a per-prompt structural-diff injection hook that kept the graph "live" by patching it every turn — rejected as a standing token cost on every turn that duplicates graphify's own parser in a second, ad hoc form.

**Docs/intent layer removed (vs 1.x).** The stack is only the four token-reducing tools. Specs/ADRs/worklogs are content, not compression; scaffolding them added a maintenance surface that drifted and a precedence tangle. Out of scope here.

**Headroom added as a fourth, proxy-layer tool (2.1).** graphify/Serena/RTK each eliminate a waste source at its origin; nothing in the original three was positioned to catch `Read`-tool file dumps or the conversation history's own growth, both of which still reach the API uncompressed. Headroom's proxy sits exactly there. See §2.4.

**Headroom's `--code-graph` and `--memory` flags never passed.** `--code-graph` would have Headroom build a second structure graph, directly duplicating graphify and reopening the layer-bleed problem §1 exists to close. `--memory` is an intent/memory feature, and this stack manages no intent layer by design (§1) — adding one back in through a flag would undo that decision by a side door. **2.3 addendum:** upstream renamed and promoted the code-graph feature — newer headroom builds a "tokensave" code graph *by default*. An upstream default change doesn't invert a deliberate decision here: the shim and wrapper pass `--no-tokensave` when the installed headroom's help advertises it (probed at install time, so older versions without the flag keep launching cleanly). Re-run `stack-init global` after upgrading headroom so the probe re-runs.

**No automatic shell alias for `claude` → `headroom wrap claude`.** The installer prints the reminder instead of writing a shell function/profile entry for it. Two reasons: editing a user's shell profile is a persistent, easy-to-miss change to their environment that this installer otherwise avoids (it only ever touches `CLAUDE.md` and `settings.json`, both Claude-owned files); and a function literally named `claude` risks recursing into itself depending on how `headroom wrap` resolves the real binary on a given shell — untested across every shell this stack targets, so it's left as an opt-in step for the human, not a default the installer commits them to. **Superseded in 2.2** by a standalone wrapper script (`clw`, falling back to `hclaude`/`claudew`) written to `~/.local/bin`: both original objections — profile mutation and self-recursion — don't apply to a distinctly-named executable that `exec`s the real binary rather than shadowing `claude` itself. **Superseded again in 2.3**: shadowing `claude` itself is now done deliberately, with the recursion hazard bounded by construction instead of avoided by naming. An absolute-path handoff turned out to be impossible — `headroom wrap` only accepts tool names (click subcommands) and re-resolves `claude` on PATH itself — so the bound comes from a re-entry guard: the shim exports `CLAUDE_STACK_SHIM` before delegating, and when headroom's PATH search lands back on the shim, that second entry execs the real binary directly (resolved by the shim, skipping its own directory) — exactly one bounce, never a loop; an already-wrapped session (localhost `ANTHROPIC_BASE_URL`) is never double-wrapped; and headroom-missing / `CLAUDE_NO_HEADROOM=1` fall through to the real binary, so the shim can degrade but never block. The profile-mutation objection is narrowed, not dismissed: one marker-guarded PATH line per rc file on Unix, one registry user-PATH prepend on Windows — both idempotent and trivially removable. Known remaining gap: launchers that spawn the binary without a PATH search (some IDE integrations) bypass the shim; the SessionStart headroom-check catches those at runtime. The 2.2 `clw` wrapper is removed as superseded (the installer deletes any it previously wrote); `headroom wrap claude` itself is the manual fallback.

**Per-repo init automated via SessionStart autobuild (2.3).** The graph is irreducibly per-repo *state*, but the per-repo *step* wasn't irreducible: a global SessionStart hook can detect "git repo, no graph" and build it in the background. Two costs were weighed. First-session surprise — minutes of background build on a big monorepo, plus a directory appearing unasked — is mitigated by backgrounding (session start is never blocked), a one-line session note so the agent knows the graph isn't ready, and two opt-outs (`CLAUDE_STACK_NO_AUTOBUILD=1`, `.graphify-skip`). Tracked-file safety is handled structurally rather than by care: the autobuild writes only under `.git/` — refresh hooks, `info/exclude` instead of `.gitignore`, a mkdir-atomic build lock (stale after 60 min, so a killed build can't wedge a repo forever) — because a background job mutating files the user would have to commit is never acceptable. The tracked-file conveniences (`.gitignore` entry, `.claude/agents/` injection) stay in `stack-init init`, where a human explicitly asked for them.

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

**Serena tool-surface audit deferred (C10, not implemented in 2.2).** If, after a few weeks of `stack-init stats` data, some Serena tools are never invoked, they could be excluded via Serena's tool include/exclude config — fewer standing tool-definition tokens and a more stable tool list (same prefix-cache-stability argument as the "compression that busts the cache" failure mode, §7). Not implemented speculatively: it's gated on real usage data that doesn't exist yet immediately after 2.2 ships.

**Rejected: per-prompt structural-diff injection.** Keeping the graph "live" by patching it every turn was rejected as a standing token cost on every turn that duplicates graphify's own parser in a second, ad hoc form — see the C2 decision entry above.

**Rejected: folding graphify into Serena's MCP server.** Would optimize subprocess launch latency (hundreds of ms) in a workflow dominated by inference latency (seconds); moves graph output out from under RTK's compression; enlarges and destabilizes Serena's tool list (cache-bust risk, same mechanism as §7's cache-busting failure mode); and requires forking upstream Serena, a maintenance surface 2.0 explicitly eliminated. §6.5's existing optional standalone graphify MCP server remains the sanctioned escape hatch if the agent under-uses the CLI-based graph.

**Rejected: a wrapper literally named `cc`.** Shadows the system C compiler and breaks `cargo`/`gcc` toolchains that resolve `cc` on PATH — the 2.2 wrapper picked `clw`/`hclaude`/`claudew` instead and never fell through to `cc`. (The wrapper itself was removed in 2.3, superseded by the shim, but the naming constraint stands for anything future that shadows a command.)

## 9. Setup verification checklist

```bash
# Global
rtk gain                                   # non-zero after a few Bash commands -> hook live
claude mcp list | grep -i serena           # registered, no --project arg
grep -q "Context routing" ~/.claude/CLAUDE.md   # contract present
command -v graphify                        # installed and on PATH
command -v headroom                        # installed and on PATH

# Per repo (after the first session's autobuild lands, or `stack-init init`)
ls -l graphify-out/graph.json              # graph built
git commit --allow-empty -m test && ls -l graphify-out/graph.json  # mtime advanced -> hook fires
git switch -c stack-check && ls -l graphify-out/graph.json  # mtime advanced -> post-checkout fires
git switch - && git branch -d stack-check
git worktree add ../stack-check-wt && cd ../stack-check-wt && git commit --allow-empty -m test \
  && ls -l graphify-out/graph.json  # THIS worktree's graph updates, not the primary checkout's

# Behavior, in a Claude session
#  - architecture question  -> reads GRAPH_REPORT.md / runs graphify, does NOT grep
#  - "who calls <fn>"        -> find_referencing_symbols, does NOT grep
#  - get_diagnostics_for_file on a planted type error -> structured error, no file dump
#  - agent tool list shows NO serena execute_shell_command / read_file
#  - one-time: break a test on purpose -> failure detail survives RTK compression
#  - repo WITHOUT graphify-out/ -> session-start note says a build is underway;
#    agent orients normally until the graph lands (no error, no manual step)
#  - `claude` in a shell with the shim on PATH -> headroom stats/logs show traffic
#    compressed and NO SessionStart Headroom NOTE (wrapped by default)
#  - `CLAUDE_NO_HEADROOM=1 claude` (or an absolute-path launch) -> the NOTE about
#    Headroom being inactive appears (shim bypassed - expected, not broken)
#  - run `stack-init stats` once -> a dated snapshot file exists under
#    ~/.claude/stack-stats/ and parses as JSON
```

**Cache-economics benchmark (manual, run once per Headroom-affecting change):**

1. Pick a fixed task shape — e.g. the same 10-turn session touching tests and edits — and run it twice against the same repo: once wrapped (bare `claude` through the shim), once bypassed (`CLAUDE_NO_HEADROOM=1 claude`).
2. Compare, from API usage / `/cost` / OTEL metrics: `input_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`, and effective cost for both runs, plus `headroom stats` for the wrapped run.
3. Acceptance: the wrapped run's *effective cost* must be ≤ the bare run's. If wire tokens dropped but cache reads collapsed, Headroom is net-negative for this usage pattern — the finding gets recorded in §8 (not silently ignored), and the recommendation becomes "prefer the bare launch" until the upstream cache-bust issue (§7) is resolved.

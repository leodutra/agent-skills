# Claude Code Context Stack — Setup & Specification

> **Version:** 2.3.3
> **Status:** Active
> **Scope:** Four tools that reduce the token cost of working in a real codebase with Claude Code — **graphify** (structure), **Serena** (symbols), **RTK** (output compression), **Headroom** (proxy-layer compression) — plus the global routing contract that makes Claude route the first three to the one thing each is best at. Headroom needs no routing decision; see §2.4. No intent/docs layer. Targets Arch Linux and Windows; Rust/TypeScript/Python.
> **Canonical executables:** `stack-init.sh` (Linux/macOS) and `stack-init.ps1` (Windows). They are self-documenting and self-installing, and they are the source of truth for **behavior** (D2). This document is the source of truth for **what the stack is and how to operate it**.
> **Rationale lives elsewhere.** Every "why" is a numbered decision in [`DECISIONS.md`](DECISIONS.md), cited here as `D<n>` and never restated. What changed and when is one line per change in [`CHANGELOG.md`](CHANGELOG.md). Three files, three jobs — the split and its enforcement are D36.
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

**Mechanism:** an MCP server wrapping real language servers (rust-analyzer, typescript-language-server, pyright) over LSP. No precomputed index of its own — it queries the live language server, so answers reflect the working tree *right now*, including uncommitted changes. **It answers nothing until a project is active:** the server is not cwd-aware and starts every session with no active project, so a per-checkout `.serena/project.yml` and an explicit `activate_project` call are both prerequisites, supplied by the serena-autoinit hook (§6.3). Confirmed tools include `find_symbol`, `find_referencing_symbols`, `get_symbols_overview`, `get_diagnostics_for_file` / `get_diagnostics_for_symbol`, and symbol-level edits (`replace_symbol_body`, `insert_after_symbol`, `insert_before_symbol`).

**Why it's in the stack:** it is the only layer that provides ground truth. `find_referencing_symbols` returns actual call sites, not text matches — no false positives from comments, strings, or look-alike methods. `get_diagnostics_for_file` returns structured compile/type/lint state without running (or paying for) a full `cargo check` dump.

**Hard boundaries (enforced by the `claude-code` context, formerly `ide-assistant`):**

1. `execute_shell_command` is **disabled** by default in `claude-code` — keep it that way. MCP tool calls bypass RTK's Bash hook; if tests ran through Serena you'd pay full uncompressed output cost. All shell goes through Claude Code's native Bash.
2. `read_file` / `search_for_pattern` are likewise disabled in `claude-code` — Claude Code provides those natively, and duplicate tools confuse routing.

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
5. Headroom's place in the stack is conditional, not assumed: it's retained only as long as the cache-economics benchmark (§8) shows it's net-positive on effective cost, not just on wire tokens (§7 "Compression that busts the prompt cache"; D20).

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
| Running tests / builds / linters / git / docker | Bash (RTK compresses automatically) | any MCP shell tool; the PowerShell tool on Windows | The RTK hook matcher is `Bash` only, so both return uncompressed output |
| Fuzzy "where's the code that handles ~concept~?" | graphify query first; Serena once a symbol name surfaces | reading many files | Graph narrows the neighborhood; LSP takes over at symbol granularity |

**Tie-breakers:**

- Question names a **specific symbol** → Serena, always.
- Question spans **more than one module** or asks about *shape* → graphify first.
- Question is about **uncommitted work-in-progress**: symbol-level → Serena (live), never graphify. Architectural → run `graphify update .` first (cheap, incremental), then query the graph as normal.
- Anything that **executes** → Bash.

Headroom doesn't appear in this matrix because it never routes a question — like RTK, it is invisible plumbing, not a layer the agent chooses to query. The only thing it requires of the human, not the agent, is launching the session correctly (§2.4, §7).

---

## 4. The routing contract `[AGENT]`

The global installer writes this contract into `~/.claude/CLAUDE.md` between sentinel markers, so re-running replaces it cleanly and touches nothing else. It is the authoritative, always-on instruction — there is no per-project copy.

The text itself is **not reproduced here**. It lives in [`contract.md`](contract.md) — the single file both installers read and `stack-init contract` prints — and the condensed form injected into agent files is [`contract-condensed.md`](contract-condensed.md). One copy is deliberate: a normative text quoted in three places drifts, and this one had already started to (the two installers disagreed on punctuation while claiming to write the same block).

The six rules in brief — 1 architecture/cross-module → graphify (conditional on a graph existing), 2 symbols → Serena, 3 diagnostics → Serena, 4 symbol-level edits → Serena, 5 anything that executes → Bash/RTK, 6 the graph reflects the last rebuild. Precedence on conflict: code/LSP (Serena) > graph (graphify).

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
2. For uncommitted symbol-level questions, the graph is silent or wrong by definition — use Serena. For uncommitted architectural questions, refresh with `graphify update .` first, then query the graph.
3. The graph is for *shape* (what connects to what); the LSP is for *fact* (what a symbol is and where it's used). A graph edge is a hypothesis about a relationship; confirm specifics at tier 1 before acting on them.

**Why precedence is explicit:** compression and cheap retrieval make every source easier to trust, including the stale one. Marking the trust order is the mitigation.

**Staleness bound:** one working-tree-moving git operation (commit, checkout, merge, or rebase) — each has its own refresh hook (§6.2), so the graph is never more than one such operation behind.

---

## 6. Installation and operating model

Most of the stack is either *configuration* (how tools behave — global by nature) or *state* (a derivation of one codebase — per-repo by nature). The split (Headroom's one exception is noted below the table):

| | Global (once, ever) | Per-repo (autobuilt; `stack-init init` = eager) |
|---|---|---|
| RTK | hook in `~/.claude/settings.json` (`rtk init -g`) | — |
| Serena | MCP registration at **user scope**, serena-autoinit SessionStart hook | `.serena/project.yml` + the activation note (autoinit, §6.3); onboarding memories (auto, first session) |
| graphify | `uv tool install graphifyy[all]`, `graphify install`, graph-autobuild SessionStart hook | `graphify .`, refresh hooks, `graphify-out/` — all autobuilt on first session |
| Headroom | `uv tool install headroom-ai[all]` + claude shim | — |
| Routing contract | `~/.claude/CLAUDE.md` (§4) | — |
| Language servers | rust-analyzer / ts-ls / pyright — once per language | — |

Two things are irreducibly per-repo *state*: the graph with its refresh hooks (there is no graph until a repo exists, and `.git/hooks` is per-repo by construction) and Serena's `.serena/project.yml` (its language-server set is derived from *this* checkout's files, and its path is what `activate_project` takes). Neither costs a per-repo *step*: a global SessionStart hook creates and maintains each — autobuild for the graph (§6.2), autoinit for the Serena project (§6.3). Headroom's activation axis (per-launch, §2.4) is likewise defaulted now: the claude shim wraps every launch that resolves `claude` on PATH, and only an explicit bypass (`CLAUDE_NO_HEADROOM=1`, an absolute-path invocation, or a shell that hasn't loaded the shim's PATH entry) skips it.

### 6.1 Global install — `stack-init` (no args)

Run once. The installer:

1. **RTK** — `cargo install` if absent, then `rtk init -g` (global Bash PreToolUse hook).
2. **Serena** — `uv tool install --from git+https://github.com/oraios/serena serena-agent`, then `claude mcp add --scope user serena -- serena start-mcp-server --context claude-code`. Three things about that command line are load-bearing:

   - **No `--project` flag** (D4). The registration is shared by every checkout, so it must be repo-agnostic. It does **not** follow that Serena finds the project itself — it is not cwd-aware and starts with no active project (§2.2, D33). Activation is a separate mechanism, installed by this same step: the **serena-autoinit SessionStart hook** (§6.3).
   - **`--context claude-code`** (the current name of the deprecated `ide-assistant`) is what disables the shell/read/search tools (§2.2, D3).
   - **A pinned binary, never `uvx --from git+…`** (D11), or a cold uv cache silently costs the session Serena entirely. The installer also migrates an existing uvx-based registration and sets `env.MCP_TIMEOUT = 120000` in `settings.json` as a safety net for a genuinely cold first launch (LSP download).

   Then it registers the serena-autoinit hook (§6.3).
3. **graphify** — `uv tool install 'graphifyy[all]'` (PyPI package is `graphifyy`, double-y; `uv tool`/`pipx` over plain `pip` because PATH issues are the most common "command not found" cause), then `graphify install` for the `/graphify` skill, then registers the **graph-autobuild SessionStart hook** (§6.2) that makes per-repo init automatic. It deliberately does **not** run `graphify claude install` (D5, D35).
4. **Headroom** — `uv tool install 'headroom-ai[all]'` (PyPI package is `headroom-ai`; same `uv tool` preference and reasoning as graphify). Installing it is necessary but not sufficient: it only takes effect for sessions launched through the proxy. So the installer shadows bare `claude` with a **recursion-safe shim** in `~/.claude/stack-bin`, prepended to PATH — on Unix via a marker-guarded line in `.profile`/`.bashrc`/`.zshrc`, on Windows via the user PATH in the registry with three shim files covering PowerShell/cmd/Git-Bash resolution. The shim bounds re-entry to exactly one bounce, never double-wraps an already-proxied session, and falls through to the real binary when headroom is missing or `CLAUDE_NO_HEADROOM=1` is set, so a broken shim can never block a session (D25). It passes `--no-tokensave` when the installed headroom advertises it, probed at install time (D26 — re-run `stack-init global` after upgrading headroom so the probe re-runs). The 2.2 `clw`/`hclaude`/`claudew` wrapper is removed as superseded and the installer deletes any it previously wrote; where the shim's PATH entry doesn't win, `headroom wrap claude` is the manual fallback (§7).
5. **Routing contract** — writes §4 into `~/.claude/CLAUDE.md` between sentinel markers (idempotent).

Prereqs: `git`, `claude` (required); `cargo`, `uv`, `pip` (for the installs); a language server per language.

### 6.2 Per-repo graph — autobuilt at session start (or `stack-init init`, eager)

Since 2.3 this is automatic. A global `SessionStart` hook (`~/.claude/hooks/graph-autobuild.sh` / `.ps1`, registered by `stack-init global`) runs at every session start inside a git repo: graph present → `graphify update .` in the background (incremental, content-hash cached, silent); graph absent → it takes a build lock (`.git/claude-stack-autobuild.lock`, mkdir-atomic, treated as stale after 60 minutes), starts `graphify .` plus the four refresh hooks below in the background, adds `graphify-out/` to `.git/info/exclude`, and injects a one-line session note that a build is underway. **Everything it writes stays under `.git/`** — a background job must never mutate tracked files, which is why it uses `info/exclude` rather than `.gitignore` and skips the `.claude/agents/` contract injection (D24). Worktree-aware: the lock lives in the worktree-private git dir (`--git-dir`), hooks and exclude in the shared one (`--git-common-dir`). Opt-outs: `CLAUDE_STACK_NO_AUTOBUILD=1` (global) or a `.graphify-skip` file in the repo root (per repo).

`stack-init init` remains as the eager variant — same graph and hooks, built in the foreground so it's ready immediately, plus the two tracked-file extras autobuild deliberately won't do: gitignoring `graphify-out/` in the repo's `.gitignore` (shareable with the team) and injecting the condensed contract into `.claude/agents/` (§6.x). Those belong in explicit, reviewable changes. A repo where neither ran still works (rule 1 is conditional).

**The four refresh hooks** (D16): `post-commit` (`graphify hook install`, incremental rebuild), `post-checkout` (branch switches only — `$3 = 1`, not per-file checkouts — backgrounded so switching isn't blocked), `post-merge`, and `post-rewrite` (fires once at the end of a rebase). All are written merge-not-clobber: an existing hook file without the stack's marker comment gets the refresh line appended rather than being overwritten.

**Worktrees:** deliberately supported, not forbidden. The triggering worktree always self-refreshes correctly; siblings catch up on their next branch switch or via rule 6's on-demand refresh (§4). Residual accepted risk in D16.

### 6.3 Per-checkout Serena project — autoinit at session start

Serena's user-scope registration is repo-agnostic by design (§6.1 step 2), which leaves two gaps that have to be closed per checkout: the server has **no project config** and **no active project**. A global `SessionStart` hook (`~/.claude/hooks/serena-autoinit.sh` / `.ps1`, registered by `stack-init global`) closes both. Inside a git repo it:

1. **Derives the language-server set from tracked files** — `git ls-files`, mapped extension → server, with compiled/checked languages emitted first because the **first entry is Serena's default and fallback server**, so a real language must outrank `markdown`/`yaml`/`toml`.
2. **Writes `.serena/project.yml`** if there isn't one, carrying a `Generated by claude-context-stack (serena-autoinit)` header.
3. **Repairs a config it didn't write** — one produced by Serena's own auto-detection — but only when that file's `language_servers` list actually *misses* a language present in this checkout, and never destructively: the original is copied to `project.yml.bak-<timestamp>` and the `project_name` it was registered under is preserved, so an intentionally renamed project doesn't silently change identity.
4. **Leaves a marker-carrying file alone permanently**, so hand edits to a generated config survive every subsequent session.
5. **Excludes `.serena/` via `.git/info/exclude`** in the *common* git dir — never a tracked `.gitignore`. Same rule the graph autobuild follows (§6.2): a background job must not mutate files the user would have to commit, and one entry in the common dir covers the main checkout and every worktree.
6. **Always ends by emitting the activation instruction** — a SessionStart `additionalContext` naming the project and its path, and stating that Serena starts with no active project so `activate_project` must be called before the first symbol query and again whenever a tool answers "No active project". This fires on every path through the hook — wrote, repaired, or found a good config already there — because writing `project.yml` does not activate it.

Why the language set is derived rather than delegated to Serena's own detection, and why repair is gated on coverage rather than on the marker: D34. Why activation is a hook rather than a registration flag: D33.

**Worktrees.** A linked worktree gets its own project (`project_serena_folder_location` is `$projectDir/.serena`), named `repo@branch` so it stays distinguishable in the path-keyed registry and the dashboard. The main checkout gets `ignored_paths: [".claude/worktrees"]`, so worktrunk's nested worktrees don't return a near-duplicate hit per branch on every symbol lookup (D33).

**Operational caveat — the language-server set is fixed per session.** Serena binds a project's language servers when it first activates that project. Editing `project.yml` afterwards, or calling `activate_project` on it again *in the same session*, does **not** reload them; the tools keep answering with the old set until a brand-new session starts. Verify a repair by reading the file, not by re-running a Serena tool in the same session.

**Opt-outs:** `CLAUDE_STACK_NO_SERENA_INIT=1` (global) or a `.serena-skip` file in the repo root (per repo). Uninstall by removing the `SessionStart` entry from `settings.json`.

### 6.4 Other subcommands

`stack-init verify` checks the wiring (RTK on PATH and hook active, Serena registered, graphify installed, graph-autobuild and serena-autoinit hooks registered, Headroom installed, claude shim first on PATH, contract present, and — in a repo — graph built, `.serena/project.yml` present, plus the post-commit and stack-owned refresh hooks installed; in a linked worktree it reports that the checkout carries its own graph and Serena project over shared hooks). It cannot check that a given session was actually launched wrapped — that's a per-launch choice, not an install-time state; the `SessionStart` headroom-check hook (§7) covers that gap at runtime instead. Nor can it confirm the agent actually *activated* the Serena project, which is likewise per-session; the autoinit hook's activation note (§6.3) is what covers that. Its repo-local checks resolve against `git rev-parse --show-toplevel`, not the current directory, so running it from a subdirectory (`config\`, as §6.5 suggests on Windows) reports the repo's real state rather than a false "not built". `stack-init contract` prints the routing contract for inspection; `stack-init contract --condensed` prints the short form injected into subagent files (§6.x). `stack-init stats` appends a dated usage snapshot for comparing stack versions (§8). `stack-init help` (also `-h`/`--help`) prints the command list — on Windows this is load-bearing rather than a courtesy, because an unrecognised flag would otherwise be swallowed as a remaining argument and leave the default `global` command to run a full unattended install.

### 6.5 Windows

`stack-init.ps1` is the Windows installer — the same `global` / `init` / `verify` / `contract` command surface and functional guarantees, equally idempotent. Platform-native integrations differ where necessary. Use PowerShell, not `cmd`: the contract write needs here-strings; batch would force `^`-escaping of every `|`/`>`/`<`/`&`. If a `cmd.exe` entry point is required, wrap it (`@powershell -ExecutionPolicy Bypass -File "%~dp0stack-init.ps1" %*`).

| Concept | Unix | Windows (PowerShell) |
|---|---|---|
| Claude config dir | `~/.claude/` | `$env:USERPROFILE\.claude\` |
| Routing contract | `~/.claude/CLAUDE.md` | `$env:USERPROFILE\.claude\CLAUDE.md` |
| Run the installer | `stack-init` | `.\stack-init.ps1` |

Notes: `graphify hook install` writes a shell post-commit hook that runs via **Git for Windows'** bundled bash (a prerequisite). The SessionStart hooks are registered as `powershell -NoProfile …`, i.e. Windows PowerShell 5.1, whose `-Encoding utf8` prepends a BOM — so serena-autoinit writes `project.yml` through an explicit no-BOM encoder, keeping it byte-identical to the POSIX variant's output rather than relying on YAML parsers tolerating a BOM (§6.3). First run may need `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. Use `graphify .`, never `/graphify .` — the leading slash is a path separator in PowerShell. Windows configures Serena's dashboard with `tray_manager`; the Unix installer leaves it manually reachable because desktop tray support is environment-dependent and untested.

### 6.x Subagents

Task-tool subagents get a fresh context that does not load `~/.claude/CLAUDE.md`. RTK's `Bash` PreToolUse hook is settings-level and applies to every session including subagents' — it propagates automatically. Headroom's env (`ANTHROPIC_BASE_URL`) is inherited by child processes — it propagates automatically too. The routing contract is neither: it's prose injected into one specific file, so subagents never see it unless something puts it there.

Mitigation (D19): `stack-init global`/`init` inject a condensed ~6-line form of the contract (rules 1, 2, 5, 6 plus the precedence line) into every `*.md` file under `~/.claude/agents/` and `.claude/agents/` respectively, between the same kind of sentinel markers used for `CLAUDE.md` (idempotent — re-running replaces the block, doesn't duplicate it). If neither directory has any agent files, the installer says so and does nothing. `stack-init contract --condensed` prints the same text for pasting into ad-hoc orchestrator prompts that spawn Task-tool subagents outside of a predefined agent file.

### 6.6 Optional — graphify MCP query server

For graph queries as MCP tools instead of CLI calls, add a `graphify` server to `.mcp.json`. The CLI (`graphify query`, `graphify path` via Bash) is the leaner default — its output flows through RTK and it adds zero always-loaded tool definitions. Add the MCP server only if the agent under-uses the graph.

---

## 7. Guardrails and known failure modes

**Layer bleed (most common).** Agent greps for a symbol, or graph-walks for a definition. Mitigation: the routing contract (§4). graphify's own PreToolUse hook (from `graphify claude install`) is *not* installed here — and not because it does nothing: it is **confirmed active** on current Claude Code and fires unconditionally on every matching Bash/Read/Glob call. It's excluded because it's unconditional where contract rule 1 is scoped to architecture questions, and because it targets the current directory's config rather than the global one (D5, D35). The contract is the mechanism, deliberately, not a hook.

**Stale graph trusted as current.** Graph reflects the last rebuild; agent reasons about mid-refactor code from it. Mitigation: precedence rule (§5) + the four refresh hooks (§6.2) bounding lag to one working-tree-moving git operation, plus rule 6's on-demand refresh before uncommitted architectural questions. `graphify update . --force` is now a fallback for anomalies (e.g. a hook failed to fire), not the primary mitigation.

**Over-compression eating a needed signal.** An RTK filter strips context the agent needed. Mitigation: RTK preserves failures in full and dumps raw output to disk on failure; run `rtk discover` periodically; verify the broken-test path once at setup. Don't pass secrets as CLI args — RTK's tracking DB stores full command strings for ~90 days.

**Shell routing around RTK.** Any MCP tool that executes commands bypasses the Bash hook, and so does Claude Code's own **PowerShell** tool on Windows — `rtk init -g` registers the PreToolUse hook with matcher `Bash`, which does not match the separate `PowerShell` tool name. Mitigation for MCP is structural (`claude-code` exposes no Serena shell tool); for PowerShell it is instructional only (§4 rule 5), because RTK's rewriter targets POSIX command lines and pointing it at PowerShell risks mangling cmdlet pipelines. If you add another MCP server with an exec tool, decide its compression story explicitly.

**Serena registered but never activated (silent).** The highest-cost failure in the stack, because nothing reports it. Serena is not cwd-aware and starts every session with no active project; if the session never calls `activate_project`, every symbol tool answers "No active project", the model falls back to grep, and contract rule 2 is unenforceable with no error surfaced to the user — the same silent shape as an MCP launch that timed out. A near-miss variant is just as quiet: a `project.yml` written by Serena's own auto-detection can list a language set that omits most of the checkout, and the tools then answer `Cannot extract symbols … Active language servers: [...]` per file. Mitigation: the serena-autoinit hook (§6.3) writes/repairs the config and re-states the activation instruction at every session start, and contract rule 2 tells the agent to call `activate_project` on that path rather than treating "No active project" as a reason to grep. Diagnosing it: check the session-start note names this checkout, read `.serena/project.yml` — and remember that a repair needs a **new session** to take effect (§6.3), so re-running a Serena tool in the same session is not a valid test.

**Hook integrity.** The only PreToolUse hook now is RTK's (`Bash`). If another tool's installer rewrites the hook array instead of merging, RTK's could be clobbered. After installing anything that touches `settings.json`, confirm the `Bash` → rtk hook is still present (`stack-init verify`).

**Headroom silently inert.** Installed but the session launched unwrapped — everything still works, just without the wire-level compression. 2.2 added a habit-sized wrapper (`clw`) and detection via a `SessionStart` hook (`~/.claude/hooks/headroom-check.sh`/`.ps1`) that checks whether `ANTHROPIC_BASE_URL` points at a local proxy and, if not, injects a one-line `NOTE: Headroom proxy not active this session...` into context. 2.3 makes prevention the default: the claude shim (§6.1 step 4) wraps bare `claude` automatically, so the NOTE now effectively means "the shim was bypassed" — a shell that hasn't loaded the shim's PATH entry, an absolute-path launch, a launcher that spawns the binary without a PATH search (some IDE integrations), or an explicit `CLAUDE_NO_HEADROOM=1`. `stack-init verify` checks the shim wins PATH resolution at install time; the SessionStart hook is what catches a live unwrapped session.

**Subagent layer bleed.** Task-tool subagents get fresh contexts that don't include `~/.claude/CLAUDE.md` — RTK's hook and Headroom's env both inherit automatically (they're settings-level / process-level), but the routing contract does not, so spawned agents can grep for symbols or orient by file-reading exactly where token volume is highest. Mitigation (§6.x "Subagents"): `stack-init global`/`init` inject a condensed ~8-line form of the contract into every file under `~/.claude/agents/` and `.claude/agents/`; orchestrator prompts for ad-hoc Task calls should paste `stack-init contract --condensed` into the subagent prompt.

**Compression that busts the prompt cache.** Headroom's wire-level rewriting is, by default, a prefix-cache invalidator: recompressing history changes the bytes the API sees turn to turn. Symptom: `headroom savings` reports savings while `cache_read_input_tokens` (from `/cost` or OTEL metrics) collapses relative to a bare session — fewer wire tokens can still mean *more* money once cache misses are priced in. A known contributor is CCR injecting a `headroom_retrieve` tool definition; changing the tool list between turns busts Anthropic's entire prefix cache regardless of what else changed. Mitigation: confirm Headroom's CacheAligner is active; check the upstream CCR/tool-injection issue status; escape hatch is running bare — RTK, Serena, and graphify are completely unaffected, since Headroom is the only optional-per-launch layer (§2.4). See §8 for the benchmark that decides whether Headroom is net-positive for a given usage pattern.

---

## 8. Setup verification checklist

```bash
# Global
rtk gain                                   # non-zero after a few Bash commands -> hook live
claude mcp list | grep -i serena           # registered, no --project arg
grep -q "Context routing" ~/.claude/CLAUDE.md   # contract present
command -v graphify                        # installed and on PATH
command -v headroom                        # installed and on PATH

# Per repo (after the first session's autobuild/autoinit lands, or `stack-init init`)
ls -l graphify-out/graph.json              # graph built
cat .serena/project.yml                    # exists; language_servers covers this checkout's
                                           # languages, a real language listed first
git commit --allow-empty -m test && ls -l graphify-out/graph.json  # mtime advanced -> hook fires
git switch -c stack-check && ls -l graphify-out/graph.json  # mtime advanced -> post-checkout fires
git switch - && git branch -d stack-check
git worktree add ../stack-check-wt && cd ../stack-check-wt && git commit --allow-empty -m test \
  && ls -l graphify-out/graph.json  # THIS worktree's graph updates, not the primary checkout's

# Behavior, in a Claude session
#  - architecture question  -> reads GRAPH_REPORT.md / runs graphify, does NOT grep
#  - session-start note names this checkout's Serena project + its path
#  - "who calls <fn>"        -> activate_project on that path, then
#                              find_referencing_symbols; does NOT grep, and does
#                              NOT treat "No active project" as a reason to grep
#  - get_diagnostics_for_file on a planted type error -> structured error, no file dump
#  - agent tool list shows NO serena execute_shell_command / read_file
#  - one-time: break a test on purpose -> failure detail survives RTK compression
#  - repo WITHOUT graphify-out/ -> session-start note says a build is underway;
#    agent orients normally until the graph lands (no error, no manual step)
#  - `claude` in a shell with the shim on PATH -> `headroom savings`/logs show traffic
#    compressed and NO SessionStart Headroom NOTE (wrapped by default)
#  - `CLAUDE_NO_HEADROOM=1 claude` (or an absolute-path launch) -> the NOTE about
#    Headroom being inactive appears (shim bypassed - expected, not broken)
#  - run `stack-init stats` once -> a dated snapshot file exists under
#    ~/.claude/stack-stats/ and parses as JSON
```

**Cache-economics benchmark (manual, run once per Headroom-affecting change):**

1. Pick a fixed task shape — e.g. the same 10-turn session touching tests and edits — and run it twice against the same repo: once wrapped (bare `claude` through the shim), once bypassed (`CLAUDE_NO_HEADROOM=1 claude`).
2. Compare, from API usage / `/cost` / OTEL metrics: `input_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`, and effective cost for both runs, plus `headroom savings` for the wrapped run (`headroom stats` is not a subcommand).
3. Acceptance: the wrapped run's *effective cost* must be ≤ the bare run's. If wire tokens dropped but cache reads collapsed, Headroom is net-negative for this usage pattern — the finding gets appended to `DECISIONS.md` (not silently ignored), and the recommendation becomes "prefer the bare launch" until the upstream cache-bust issue (§7) is resolved.

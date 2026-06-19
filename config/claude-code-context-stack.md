# Claude Code Context Stack — Setup & Specification

> **Version:** 1.2
> **Status:** Active
> **Scope:** Claude Code context stack — graphify (structure), Serena (symbols), RTK (output compression), docs layer (intent). Targets Arch Linux; Rust/TypeScript/Python projects. §4 documents each component's per-project configuration in full; §10 is the operating model: install the global layer once, then bootstrap each repo with `stack-init`.
> **Changelog:** 1.2 — added §10.6 (Windows / PowerShell) and `stack-init.ps1`; 1.1 — added §10 (global single-setup + per-project bootstrap); 1.0 — initial.
> **Audience:** Both the human installing it and the agent operating inside it. Sections marked `[AGENT]` are meant to be referenced from CLAUDE.md.

---

## 1. Purpose and design principle

Claude Code's effectiveness on a real codebase is bounded by context quality, not model intelligence. Context degrades from five distinct sources of waste, and each tool in this stack eliminates exactly one of them:

| Waste source | What it looks like | Owned by |
|---|---|---|
| **Orientation** | Re-reading dozens of files to learn what connects to what | graphify |
| **Retrieval & editing** | Whole-file dumps, grep walls, regex edits that miss aliased refs | Serena |
| **Tool-output noise** | 5,000 tokens of passing-test boilerplate per `cargo test` | RTK |
| **Intent re-derivation** | Re-explaining what we're building and why, every session | SPEC.md + ADRs + roadmap |
| **Convention re-derivation** | Re-litigating house style, idioms, error-handling rules | Project skill |

The design principle: **each layer owns one question, no layer answers another layer's question.** Most failure modes in this stack come from layer bleed — the agent BFS-ing the graph for a symbol lookup, or running tests through an MCP shell that bypasses RTK. The configuration below makes the boundaries structural where possible and instructional (CLAUDE.md rules) where not.

A second principle, inherited from how the layers differ epistemically: **sources have tiers of truth.** The LSP is ground truth by construction (it is the compiler's model). The graph is a deterministic but potentially stale derivation. The spec is *intent*, not fact. Precedence rules in §5 make this explicit so the agent never builds on a stale or aspirational source while believing it is current fact.

---

## 2. Component roles and hard boundaries

### 2.1 graphify — the map (structure)

**Answers:** "What connects X to Y?", "What's the blast radius of touching Z?", "How is this codebase organized?", "Where should I even start looking?"

**Mechanism:** tree-sitter parses code locally (zero API calls), producing a typed graph of files/functions/classes/tables with contain/import/invoke edges, persisted as `graphify-out/graph.json` plus a human/agent-readable `GRAPH_REPORT.md` (god nodes, communities, surprising connections). SHA256 cache means incremental rebuilds only touch changed files.

**Why it's in the stack:** it converts the most expensive operation in agentic coding — cold orientation on a large repo — into a one-time build plus cheap queries. Its value is front-loaded: first sessions, unfamiliar areas, cross-module tracing, refactor impact analysis.

**Hard boundary:** graphify is NOT for targeted symbol lookup. Measured sessions show a graph BFS returning ~1,500 tokens for queries Serena answers in a fraction of that. If the question names a specific symbol, it is not a graphify question.

**Staleness model:** the graph is a snapshot. It is rebuilt by a git post-commit hook (§4.3), so it is correct as of the last commit — *never* correct for uncommitted work-in-progress. This is the key limitation the agent must know: **the graph trails the working tree.**

### 2.2 Serena — the eyes and hands (symbols)

**Answers:** "Where is symbol S defined?", "Who references S?", "What implements trait T?", "Does this file have errors?", and performs symbol-precise edits (`replace_symbol_body`, `insert_after_symbol`, `rename_symbol`).

**Mechanism:** an MCP server wrapping real language servers (rust-analyzer, typescript-language-server, pyright) over LSP. No precomputed index of its own — it queries the live language server, so its answers reflect the working tree *right now*, including uncommitted changes.

**Why it's in the stack:** it is the only layer that provides ground truth. `find_referencing_symbols` returns actual call sites, not text matches — no false positives from comments, strings, or same-named methods on unrelated types. `get_diagnostics_for_file` returns structured compile/type/lint state without running (or paying for) a full `cargo check` dump.

**Hard boundaries:**
1. Serena's `execute_shell_command` stays **disabled** (it is disabled by default in the `ide-assistant` context — keep it that way). Reason: MCP tool calls bypass RTK's Bash hook. If tests run through Serena, you pay full uncompressed output cost. All shell goes through Claude Code's native Bash.
2. Serena's `read_file` / `search_for_pattern` also stay disabled in `ide-assistant` context — Claude Code already has those natively, and duplicate tools confuse routing.

### 2.3 RTK — the filter (output compression)

**Answers:** nothing. RTK is invisible plumbing. It intercepts every Bash command via a PreToolUse hook, rewrites `git status` → `rtk git status`, and the model receives 60–90% fewer tokens of output. Failures, errors, diffs, and stack traces are preserved in full; the compression targets boilerplate and pass-noise.

**Why it's in the stack:** test/build/git/tooling output is the single largest uncontrolled token sink in a session. `cargo test` compresses ~92%, `git status` ~81%. Over a session this is the difference between one context window and three.

**Two usage modes:**
- **Output mode (automatic, primary):** the PreToolUse hook. Zero workflow change.
- **Input mode (manual, for deliberate context assembly):** call filters directly and capture stdout when constructing context on purpose — `rtk ls src/`, `rtk git log -n 20`, `rtk read path/to/file`, `rtk grep pattern`. Use this when writing prompts, session-start summaries, or feeding compressed state into subagents. (A first-class "inject into prompt at position X" mode is an open upstream feature request, not shipped — the manual capture pattern is the supported path today.)

**Hard boundary:** RTK compresses output of ~100 known dev commands. It is not a semantic/prose compressor — it will not shrink the spec, markdown, or arbitrary text. Don't ask it to.

### 2.4 Docs layer — the why (intent)

`SPEC.md` (thin index + invariants), `docs/adr/` (durable decisions), `ROADMAP.md` (priorities), `docs/worklog.md` (session-to-session continuity: what was tried, what was rejected, what's mid-flight). Detailed in §6.

### 2.5 Project skill — the how (conventions)

The local skill (`.claude/skills/<project>/SKILL.md`) carries house rules: idiomatic patterns, error-handling policy, the routing rules from §3, and the precedence rules from §5. It is the one document loaded every session, so it must stay thin — an index with pointers, not a textbook.

---

## 3. `[AGENT]` Routing matrix

This is the core decision table. Route every information need to exactly one layer.

| Question shape | Route to | NOT to | Why |
|---|---|---|---|
| "How is this organized / what's the architecture?" | graphify (`GRAPH_REPORT.md`, `graphify query`) | reading files, grep | Orientation is precomputed; reading files to orient burns 10–50x the tokens |
| "What connects A to B?" / "what's between these modules?" | graphify (`graphify path A B`) | grep, Serena | Multi-hop relationships are graph traversals; LSP sees one hop at a time |
| "Blast radius if I change X?" (module/system level) | graphify first, then Serena to confirm exact refs | grep | Graph gives the community-level spread; LSP confirms precise call sites |
| "Where is symbol S defined / who calls S?" | Serena (`find_symbol`, `find_referencing_symbols`) | graphify, grep | LSP is exact and current; graph may be stale, grep has false positives |
| "What implements trait/interface T?" | Serena (`find_implementations`) | grep | Only the LSP resolves this correctly |
| "What's in this file?" (structure, not content) | Serena (`get_symbols_overview`) | reading the whole file | Overview costs a fraction of a full read |
| "Does this compile / what are the type errors?" | Serena (`get_diagnostics_for_file`) | running `cargo check` via Bash | Diagnostics are structured and already minimal; no compression heuristics involved |
| Editing a function/class body | Serena (`replace_symbol_body`, `insert_*_symbol`) | regex/string replace | Symbol-anchored edits don't hit comments, strings, or look-alike names |
| Renaming across the codebase | Serena (`rename_symbol`) | search-and-replace | Atomic, LSP-verified, no missed aliased imports |
| Running tests / builds / linters / git / docker | Bash (RTK compresses automatically) | Serena shell (disabled) | RTK hook only covers Bash; MCP shell would bypass it |
| "Why is it built this way / what are we building?" | SPEC.md index → pull the specific section or ADR | guessing from code | Code says what, never why; the why lives in the docs layer |
| "What did we decide about X?" | `docs/adr/` index | re-deriving | Decisions are append-only records; re-deriving risks contradicting them |
| "What was tried last session / what's in flight?" | `docs/worklog.md` | conversation memory | Worklog survives session boundaries; memory doesn't |
| "What are the house idioms / conventions?" | project skill | inferring from code samples | Inferring re-derives (inconsistently) what is already written down |
| Fuzzy "where's the code that handles ~concept~?" | graphify query first; Serena once a symbol name surfaces | reading many files | Graph narrows the neighborhood; LSP takes over at symbol granularity |

**Tie-breakers:**
- Question names a **specific symbol** → Serena, always.
- Question spans **more than one module** or asks about *shape* → graphify first.
- Question is about **uncommitted work-in-progress** → Serena or direct reads, never graphify (graph trails the working tree).
- Anything that **executes** → Bash.

---

## 4. Installation and configuration

All steps assume Arch Linux, per-project setup, repo root as CWD.

### 4.1 RTK

```bash
# Install (Rust-native; cargo preferred on Arch)
cargo install --git https://github.com/rtk-ai/rtk
# or: curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh

# Register the global PreToolUse hook for Claude Code
rtk init -g
```

What `rtk init -g` does: installs a PreToolUse hook (matcher: `Bash`) in Claude Code's `settings.json` that rewrites supported commands to their `rtk` equivalents before execution. The agent never knows; it just receives cleaner output.

**Post-install checks:**

```bash
rtk --version
rtk gain          # token-savings stats; confirms hook is live after a few commands
rtk discover      # audit: surfaces commands with suspiciously low savings (mis-filtering signal)
```

**Operational notes (the whys):**
- On test failure, RTK preserves failure detail and writes full unfiltered output to disk for retrieval. Verify this once on a deliberately broken test: passing tests are noise, failing tests are the entire signal. If a filter ever flattens a failure you needed, that command can be excluded from rewriting in RTK's config.
- RTK's tracking DB (`~/.local/share/rtk/tracking.db`) stores full command strings for ~90 days. Don't pass secrets as CLI args (you shouldn't anyway); a reported issue notes bearer tokens/passwords in args persist verbatim.
- Telemetry: check `rtk telemetry status` and disable if undesired.

### 4.2 Serena

Prerequisite: `uv` installed (`pacman -S uv`), plus language servers for the project's languages. rust-analyzer ships with rustup (`rustup component add rust-analyzer`); TypeScript and Python servers are fetched/managed per Serena's language support docs.

```bash
# Register Serena as an MCP server for this project
claude mcp add serena -- uvx --from git+https://github.com/oraios/serena \
  serena start-mcp-server --context ide-assistant --project "$(pwd)"
```

**Why `--context ide-assistant`:** this context exposes only Serena's unique value (symbol retrieval, symbol edits, diagnostics, memories) and disables `read_file`, `search_for_pattern`, and `execute_shell_command` — all three of which Claude Code already provides natively. This is what enforces the §2.2 boundary structurally instead of by instruction: shell *cannot* route around RTK because Serena has no shell tool exposed.

**First run:** Serena performs onboarding (analyzes project structure, stores notes under `.serena/memories/`). Let it complete once; subsequent sessions read memories selectively. Then verify `.serena/project.yml` exists and review:

```yaml
# .serena/project.yml — relevant keys
read_only: false        # true = analysis-only mode (disables all editing tools)
ignored_paths:
  - graphify-out        # don't let the LSP layer index graph artifacts
  - target
  - node_modules
```

**Verification:** in a Claude Code session, ask it to `find_symbol` something you know exists, and `get_diagnostics_for_file` on a file with a deliberate type error. Both should return structured results, not file dumps.

### 4.3 graphify

```bash
# Install — note the PyPI package is graphifyy (double y)
pip install 'graphifyy[all]'     # full: MCP + PDF/office/video parsing + community detection
graphify install                  # registers the /graphify skill at ~/.claude/skills/
graphify claude install --project # project-scoped Claude Code integration

# Build the initial graph
graphify .

# Keep it fresh automatically: git post-commit hook rebuilds incrementally
graphify hook install

# Keep artifacts out of the index/repo (solo project — commit it only if a team queries it)
echo -e "\n# Knowledge graph outputs\ngraphify-out/" >> .gitignore
```

What `graphify claude install` does: writes a CLAUDE.md directive ("read `graphify-out/GRAPH_REPORT.md` before answering architecture questions") and installs a PreToolUse hook on `Glob`/`Grep` that reminds the agent a graph exists before it starts file-scanning.

**Hook coexistence (important):** you now have two PreToolUse hooks — RTK on matcher `Bash`, graphify on matcher `Glob`/`Grep`. Different matchers, no collision. Verify both are present in `settings.json` after install; some installers rewrite rather than merge hook arrays. If one clobbered the other, re-run the clobbered tool's init.

**Update policy (the why):** `graphify update .` belongs in *git hooks*, not Claude Code hooks — rebuilding on every agent action would thrash; rebuilding on commit matches the graph's epistemic status as "correct as of last commit." Full rebuild (`graphify update . --force`) after branch switches or large refactors.

**Optional — MCP query server:** for graph queries as tools instead of CLI calls:

```json
// .mcp.json
{
  "mcpServers": {
    "graphify": {
      "command": "python",
      "args": ["-m", "graphify.serve", "graphify-out/graph.json"]
    }
  }
}
```

CLI (`graphify query "..."`, `graphify path A B` via Bash) is the leaner default — it flows through RTK and adds zero always-loaded tool definitions. Add the MCP server only if you find the agent under-using the graph.

### 4.4 CLAUDE.md — the routing contract

`graphify claude install` writes its own section; keep it, and add this block (or point to the skill that contains it):

```markdown
## Context routing (non-negotiable)

1. Architecture / cross-module / "what connects X to Y" / blast radius
   → read graphify-out/GRAPH_REPORT.md or run `graphify query` / `graphify path`.
   NEVER orient by reading files or grepping.
2. Specific symbols: definitions, references, implementations, file overviews
   → Serena (find_symbol, find_referencing_symbols, get_symbols_overview).
   NEVER grep for symbol names.
3. Compile/type/lint state → Serena get_diagnostics_for_file.
   Do NOT run `cargo check` for information diagnostics already provide.
4. Code edits to existing symbols → Serena symbol-level edit tools,
   not string replacement.
5. Tests, builds, git, anything that executes → Bash (RTK compresses it).
6. Intent ("why", "what are we building") → SPEC.md index, then pull only
   the referenced section/ADR. Never load the full spec.
7. Before assuming prior context: check docs/worklog.md.
8. The graph reflects the LAST COMMIT. For uncommitted work, use Serena.

## Source-of-truth precedence (on conflict)

code/LSP (Serena)  >  graph (graphify)  >  SPEC.md/ADRs (intent)  >  memories/worklog

If the spec contradicts the code: the code is the fact, the spec is the intent.
Do NOT silently reconcile. Flag the divergence, ask whether to fix code toward
spec or update spec toward code. Record the resolution in the worklog.

## Session hygiene

- End of significant sessions: append to docs/worklog.md — what changed,
  what was tried and rejected (with the reason), what is mid-flight.
- A decision that will outlive the month → propose an ADR, don't bury it
  in the worklog.
```

---

## 5. `[AGENT]` Precedence and divergence — the epistemic spec

The five context sources can disagree. Tiered by how they acquire truth:

| Tier | Source | Epistemic status | Staleness |
|---|---|---|---|
| 1 | Serena / LSP | Ground truth — the compiler's live model | Never (live working tree) |
| 2 | graphify graph | Deterministic derivation of committed code | Trails working tree by ≤1 commit (hook) |
| 3 | SPEC.md + ADRs | **Intent** — what should be true | Stale whenever code moved without a spec update |
| 4 | Serena memories, worklog | Observations and notes | Informal; verify before relying |

**Rules:**
1. A tier-3 claim about code (signatures, types, structure) is a *hypothesis* until confirmed at tier 1. Never implement against a spec-stated signature without a `find_symbol` confirmation when the code already exists.
2. Tier 2 vs tier 1 conflict → the graph is stale; trust the LSP, note that a rebuild is due.
3. Tier 1 vs tier 3 conflict → **divergence event**: stop, flag, ask direction (code→spec or spec→code), record in worklog. Silent reconciliation is the prohibited move — it hides drift until it compounds.
4. Tier 4 never overrides anything; it only points at where to look.

**Why this matters more in this stack, not less:** compression and cheap retrieval make every source *easier* to trust, including the stale ones. The cheaper a wrong answer is to obtain, the more explicitly its trust level must be marked. This table is the mitigation.

---

## 6. The docs layer — structure and grooming rules

```
project/
├── CLAUDE.md                  # thin: routing contract + pointers (§4.4)
├── SPEC.md                    # thin index + invariants (see below)
├── ROADMAP.md                 # phases, priorities, current focus
├── docs/
│   ├── adr/
│   │   ├── INDEX.md           # one line per ADR: id, title, status
│   │   └── NNN-title.md       # context / decision / consequences; append-only
│   ├── spec/                  # deep spec sections, pulled on demand
│   │   ├── domain-model.md
│   │   ├── api-surface.md
│   │   └── ...
│   └── worklog.md             # session continuity (newest first)
└── .claude/skills/<project>/
    └── SKILL.md               # conventions + routing rules; thin index
```

**SPEC.md is an index, not a document.** It contains, in order: (1) one-paragraph project statement; (2) **invariants** — the short list of things that must never be violated, each phrased so a fitness function or lint can check it ("all public functions return `Result`", "no `unwrap` outside tests"), not aspirational prose; (3) the section index — one line per deep-spec file with a when-to-read trigger ("touching persistence → read docs/spec/storage.md, ADR-014"); (4) **non-goals**; (5) **open decisions** — explicitly unsettled questions, so the agent never hallucinates a choice into a gap and presents it as settled.

**Epistemic tags in spec sections.** Mark each section header: `[INVARIANT]` (must hold, agent may never violate), `[AS-BUILT]` (describes current implementation, code wins on conflict), `[PROPOSED]` (not yet implemented, do not assume it exists). This is the four-tier provenance idea applied to your own docs: the agent must know which lines are constraints and which are snapshots.

**One fact, one home.** Any value stated in both spec and ADR (a threshold, a port, a schema field) will eventually diverge. State it once; reference it everywhere else.

**Worklog format** — three lines per session is enough:

```markdown
## 2026-06-12
- Done: extracted retry policy into `net::retry`; wired through `Client`.
- Rejected: tower middleware approach — fought the existing error type (see attempt on branch wip/tower-retry).
- In flight: backoff jitter untested; property test sketched in tests/retry_prop.rs.
```

The "rejected, with reason" line is the highest-value line in the file: it is the only thing preventing a future session from re-proposing last week's dead end.

---

## 7. Guardrails and known failure modes

**Layer bleed (most common).** Agent greps for a symbol, or graph-walks for a definition. Mitigation: routing contract in CLAUDE.md (§4.4) + graphify's Glob/Grep hook nudge. If it persists for a class of query, add that query shape to the contract explicitly.

**Stale graph trusted as current.** Graph reflects last commit; agent reasons about mid-refactor code from it. Mitigation: rule 8 in the contract; post-commit hook keeps the lag to one commit; `--force` rebuild after branch switches.

**Over-compression eating a needed signal.** An RTK filter strips context the agent needed. Mitigation: RTK preserves failures in full by design and dumps raw output to disk on failure; run `rtk discover` periodically; verify the broken-test path once at setup (§4.1).

**Shell routing around RTK.** Any MCP tool that executes commands bypasses the Bash hook. Mitigation: structural — `ide-assistant` context exposes no Serena shell tool. If you ever add another MCP server with an exec tool, decide its compression story explicitly.

**Spec bloat reversing the savings.** The docs layer grows until front-loading it costs more than RTK + Serena save. Mitigation: SPEC.md stays an index; deep sections are pull-on-demand; CLAUDE.md stays under roughly a screen.

**Silent drift between intent and code.** Mitigation: divergence rule (§5.3) + phrasing invariants so they're mechanically checkable — wire cargo-cognate / idiom lints as the enforcement, so spec and reality agree by construction rather than by vigilance.

**Hook clobbering.** A tool's installer rewrites the PreToolUse array instead of merging. Mitigation: after any (re)install of rtk or graphify integration, inspect `settings.json` and confirm both matchers (`Bash`; `Glob`/`Grep`) are present.

---

## 8. Setup verification checklist

```bash
# RTK live?
rtk gain                          # non-zero stats after a few Bash commands in a session

# Hooks intact?
grep -A4 PreToolUse ~/.claude/settings.json   # expect Bash (rtk) AND Glob/Grep (graphify)

# Serena answering?
#   in-session: find_symbol on a known symbol → structured result, no file dump
#   in-session: get_diagnostics_for_file on a file with a planted type error → the error, structured

# Serena boundaries enforced?
#   in-session: agent tool list shows NO serena execute_shell_command / read_file

# Graph fresh?
ls -l graphify-out/graph.json     # mtime ≈ last commit
git commit --allow-empty -m test && ls -l graphify-out/graph.json   # mtime advanced → hook works

# Failure-signal preservation (one-time):
#   break a test on purpose; confirm the failure detail survives RTK compression

# Routing behaving?
#   ask an architecture question → agent reads GRAPH_REPORT.md / runs graphify query, does not grep
#   ask "who calls <fn>" → agent uses find_referencing_symbols, does not grep
```

---

## 9. Decisions log (the whys, condensed)

**Serena in `ide-assistant` context, shell disabled** — makes the RTK-bypass impossible structurally rather than by instruction; removes duplicate read/search tools that confuse routing.

**graphify rebuild on git post-commit, not on agent hooks** — matches the graph's epistemic status ("true as of last commit"), avoids rebuild thrash, keeps staleness bounded and *known* rather than variable.

**graphify via CLI through Bash by default, MCP server optional** — CLI output flows through RTK and costs zero standing tool definitions; MCP adds value only if the agent under-uses the graph.

**Diagnostics from Serena, not from compressed `cargo check`** — structured LSP data is already minimal and involves no lossy heuristic; compression belongs where output is noisy, not where it's already signal.

**RTK input mode = manual `$(rtk ...)` capture** — the first-class prompt-injection mode is an unshipped upstream proposal; the manual pattern is the supported equivalent and keeps you in control of placement.

**Spec as tiered index, not loaded document** — front-loading durable context would consume the budget the compression layers free up; progressive disclosure preserves it. Epistemic tags + precedence rules exist because cheap retrieval makes stale sources *more* dangerous, not less.

**Worklog separate from ADRs** — ADRs are durable, append-only decisions; the worklog is ephemeral continuity (including rejected attempts). Merging them either bloats the ADR record or loses the "we already tried that" signal.

---

## 10. Single global setup — one install, every project

§4 remains the authoritative reference for what each component's configuration *means*. This section reorganizes those same steps into the operating model: a **global layer** installed exactly once, and a **per-project residue** collapsed into one idempotent script (`stack-init`, shipped alongside this doc — the script is the canonical executable; this section describes it, it does not duplicate it).

### 10.1 Why the split falls where it does

Everything in the stack is either *configuration* (how tools behave — global by nature) or *state* (derivations and content of one codebase — per-project by nature):

| | Global (config) | Per-project (state) | Why it can't move |
|---|---|---|---|
| RTK | hook in `~/.claude/settings.json` (`rtk init -g`) | — | matcher `Bash` already applies everywhere |
| Serena | MCP registration at user scope | `.serena/project.yml`, onboarding memories | memories describe one repo's structure |
| graphify | `pip install`, `graphify install`, `graphify claude install` | `graphify .`, post-commit hook, `graphify-out/` | the graph is a derivation of *a* codebase; `.git/hooks` is per-repo by construction |
| Routing contract | `~/.claude/CLAUDE.md` (§4.4 content) | thin project `CLAUDE.md` (pointers only) | rules are universal; pointers are content |
| Docs layer | template (inside `stack-init`) | SPEC.md, ADRs, worklog, ROADMAP | it *is* the project's content |
| Language servers | rust-analyzer, ts-ls, pyright — once per language | — | the LSP serves any repo in that language |

### 10.2 Global layer (run once, ever)

```bash
# RTK — global Bash PreToolUse hook
cargo install --git https://github.com/rtk-ai/rtk
rtk init -g

# Serena — user scope, NO --project flag (the one delta vs §4.2):
# pinning --project at registration binds the server to a single repo.
# Registered bare, Serena activates the project from the session's cwd
# (or via its activate_project tool), so one registration serves all repos.
claude mcp add --scope user serena -- uvx --from git+https://github.com/oraios/serena \
  serena start-mcp-server --context ide-assistant

# graphify — skill + Claude integration at global scope
pip install 'graphifyy[all]'
graphify install
graphify claude install

# Language servers — once per language
rustup component add rust-analyzer
# + typescript-language-server / pyright per Serena's language docs

# Routing contract — promote the §4.4 block to ~/.claude/CLAUDE.md
# with ONE amendment (see 10.4): graphify rules become conditional.
```

### 10.3 Per-project bootstrap — `stack-init`

Run once from a repo root; idempotent (re-runs only fill gaps, never overwrite spec/worklog content). It performs, in order: `graphify .` (initial graph) → `graphify hook install` (post-commit incremental rebuild) → gitignore `graphify-out/` → write `.serena/project.yml` with standard ignores (Serena onboards itself on the first agent session) → scaffold the §6 docs layer (SPEC.md index with epistemic tags, `docs/adr/INDEX.md`, `docs/worklog.md`, `ROADMAP.md`) → write a *thin* project `CLAUDE.md` containing only pointers (the contract itself lives globally) → verify graph artifact, post-commit hook, rtk on PATH, and Serena registration.

End state: **install once + `stack-init` once per repo** → every session in every project gets identical routing behavior with zero per-session setup.

### 10.4 Deltas the global arrangement introduces

**The contract outruns the bootstrap.** `~/.claude/CLAUDE.md` applies even in repos where `stack-init` never ran — the agent would be ordered to consult a graph that doesn't exist. Amend rule 1 of the §4.4 contract when promoting it to global:

```markdown
1. Architecture / cross-module / blast radius:
   IF graphify-out/ exists → read GRAPH_REPORT.md or run `graphify query`/`graphify path`;
   never orient by reading files or grepping.
   IF it does not exist → orient normally, and suggest running `stack-init` once.
```

Un-bootstrapped repos degrade gracefully instead of erroring; the agent itself nudges toward bootstrap.

**Serena first-session cost moves, not disappears.** One user-scope server serves whatever repo the cwd points at; per-project memories stay in each repo's `.serena/`, so there is no cross-project contamination — but the first session in a fresh repo pays onboarding time. Right trade: once per project, not once per registration, and never per session.

**Multi-language becomes free.** Nothing in the global layer is language-pinned; the same setup covers Rust, TypeScript, and Python projects with no per-project language work. The only language cost is the LSP install, paid once ever (10.2).

**Project skill becomes optional, not default.** With the routing contract global, a per-project `.claude/skills/` entry is only warranted when a repo has conventions that genuinely diverge from your house defaults. Default to nothing; add when divergence is real. (This is §7's spec-bloat guardrail applied to skills.)

### 10.5 Verification additions (beyond §8)

```bash
# Global contract present?
grep -q "Context routing" ~/.claude/CLAUDE.md

# Serena at user scope (not project-pinned)?
claude mcp list | grep -i serena        # registration should show no --project arg

# Graceful degradation: in a repo WITHOUT graphify-out/, ask an architecture
# question → agent orients normally and suggests stack-init (does not error,
# does not pretend a graph exists).

# Cross-project isolation: .serena/memories/ in repo A contains nothing about repo B.
```

### 10.6 Windows

The global layer (10.2) is cross-platform as written — `cargo install`, `rtk init -g`, `claude mcp add`, `pip install`, `graphify install`, and `rustup component add` run identically in PowerShell. Only paths and the bootstrap script differ.

**Use PowerShell, not cmd.** `stack-init.ps1` is the Windows bootstrap. Classic `cmd.exe`/batch is a poor fit because the script generates multi-line markdown/YAML and batch has no heredoc — every `|`/`>`/`<`/`&` would need `^`-escaping. If a `cmd.exe` entry point is required, wrap it: a one-line `stack-init.bat` containing `@powershell -ExecutionPolicy Bypass -File "%~dp0stack-init.ps1" %*`. (`graphify hook install` writes a shell post-commit hook; it runs via Git for Windows' bundled bash, so Git for Windows is a prerequisite.)

**Path translations:**

| Concept | Unix | Windows (PowerShell) |
|---|---|---|
| Claude config dir | `~/.claude/` | `$env:USERPROFILE\.claude\` |
| Global routing contract | `~/.claude/CLAUDE.md` | `$env:USERPROFILE\.claude\CLAUDE.md` |
| Bootstrap on PATH | `~/.local/bin/stack-init` | any dir on `$env:PATH` (e.g. `$env:USERPROFILE\bin\stack-init.ps1`) |
| Run the bootstrap | `stack-init` | `stack-init.ps1` (or `pwsh -File stack-init.ps1`) |

**Behavioral parity:** the `.ps1` mirrors the `.sh` step-for-step and is equally idempotent. The only intentional difference is the post-commit verification — Windows has no execute bit, so the check is existence (`Test-Path .git\hooks\post-commit`) rather than executability.

**ExecutionPolicy:** first run may require `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` (or invoke with `-ExecutionPolicy Bypass`). This is a one-time, user-scoped allowance.

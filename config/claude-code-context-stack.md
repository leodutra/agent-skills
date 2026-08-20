# Claude Code Context Stack — Setup & Specification

> **Version:** 3.0
> **Status:** Active
> **Scope:** Two components — **Serena** (LSP symbol tools, opt-in per session; D53) and **ponytail** (minimal-code discipline, default-on; D54) — plus the global routing contract. 3.0 removed graphify, RTK, and Headroom (D51, D52): the stack no longer intercepts anything, holds no per-repo state, and adds no compression layer. Orientation and tool-output noise are explicitly unowned (§2.3). No intent/docs layer. Targets Arch Linux and Windows; Rust/TypeScript/Python.
> **Canonical executables:** `stack-init.sh` (Linux/macOS) and `stack-init.ps1` (Windows). They are self-documenting and self-installing, and they are the source of truth for **behavior** (D2). This document is the source of truth for **what the stack is and how to operate it**.
> **Rationale lives elsewhere.** Every "why" is a numbered decision in [`DECISIONS.md`](DECISIONS.md), cited here as `D<n>` and never restated. What changed and when is one line per change in [`CHANGELOG.md`](CHANGELOG.md). Three files, three jobs — the split and its enforcement are D36.
> **Audience:** Both the human installing it and the agent operating inside it. Sections marked `[AGENT]` are mirrored into the global routing contract.

---

## 1. Purpose and design principle

Claude Code's effectiveness on a real codebase is bounded by context quality, not model intelligence. Earlier versions of this stack tried to control that by owning four sources of waste at once. 3.0 owns far less, on purpose:

| Waste source | What it looks like | Owned by |
|---|---|---|
| **Retrieval & editing** | Whole-file dumps, grep walls, regex edits that miss aliased refs | Serena — **only when enabled** (§2.1, D53) |
| **Code that didn't need writing** | Wrappers, abstraction layers, "future-proofing" the task didn't ask for | ponytail (§2.2, D54) |
| **Orientation** | Re-reading dozens of files to learn what connects to what | *unowned* since 3.0 (D52) |
| **Tool-output noise** | Thousands of tokens of passing-test boilerplate per `cargo test` | *unowned* since 3.0 (D51) |
| **Wire-level residue** | `Read`-tool file dumps, growing conversation history | *unowned* since 3.0 (D51) |

Three design principles:

**One question per layer; no layer answers another layer's question.** The classic failure mode is *layer bleed* — grepping for a symbol name while an LSP is loaded. With only one routing layer left, the surface for bleed is small, and the contract's job shifts from arbitrating between tools to knowing whether the one optional tool is even present (§4 rule 1).

**Eliminate at the source; never compress downstream.** This is the lesson 3.0 was built on, and it was paid for. Serena and ponytail both remove waste where it originates — one by answering precisely instead of dumping, the other by not generating the code in the first place. The stack previously carried two downstream compressors, and measurement killed both: a layer that rewrites bytes already in the request competes with the provider's prefix cache and loses by roughly 10× when it does, and a layer that reports its own savings cannot be trusted without an independent check — one of them was inflating its number ~4× while every standing health check read green (D49, D50, D51).

**Prefer instructing over intercepting.** Every layer removed in 3.0 sat in a path: RTK before the shell, Headroom before the API, graphify on disk. Each broke in a way that was a property of *being there* — a mangled command, a poisoned response cache, a stale artifact trusted as current. ponytail is the counter-example and the template: its entire mechanism is text reaching the model, so its worst failure is that the text is unhelpful (D54).

What this stack deliberately does **not** do: manage intent (specs, ADRs, roadmaps) or conventions. Those are valuable but they are not context *compression* — they are content, and earlier versions that scaffolded them added a maintenance surface that drifted. It also, since 3.0, does not carry per-repo state of any kind: no graph, no derived artifact, nothing to rebuild or invalidate.

---

## 2. Component roles and hard boundaries

### 2.1 Serena — the eyes and hands (symbols), opt-in

**Answers:** "Where is symbol S defined?", "Who references S?", "What's in this file?", "Does this file have errors?", and performs symbol-precise edits — **in sessions that enable it.**

**Mechanism:** an MCP server wrapping real language servers (rust-analyzer, typescript-language-server, pyright) over LSP. No precomputed index of its own — it queries the live language server, so answers reflect the working tree *right now*, including uncommitted changes. **It answers nothing until a project is active:** the server is not cwd-aware and starts every session with no active project, so a per-checkout `.serena/project.yml` and an explicit `activate_project` call are both prerequisites; the serena-autoinit hook (§6.3) supplies the first so an enabled session is immediately usable. Confirmed tools include `find_symbol`, `find_referencing_symbols`, `get_symbols_overview`, `get_diagnostics_for_file` / `get_diagnostics_for_symbol`, and symbol-level edits (`replace_symbol_body`, `insert_after_symbol`, `insert_before_symbol`).

**Why it's in the stack:** it is the only layer that provides ground truth. `find_referencing_symbols` returns actual call sites, not text matches — no false positives from comments, strings, or look-alike methods. `get_diagnostics_for_file` returns structured compile/type/lint state without running (or paying for) a full `cargo check` dump.

**Why it is off by default (D53, D55):** its cost profile is not flat. It is reported to lose on cheap lookups — roughly 4× the cost of simply answering — and to win on deep modification work in large codebases. Its tool manifest is a fixed per-session tax, **measured at 5,791 tokens** across 24 tools in the `claude-code` context (Serena's default context is 8,299 across 30; the six tools §2.1 boundary 1–2 exclude are 2,508 of them). That is ~4× *smaller* than the ~24K originally cited, and D55 records the correction.

So the case for opt-in is not that the manifest is huge. Tool definitions render **first** in Anthropic's cache prefix, so in steady state those tokens are read at ~0.1× and cost little. The real reasons are that a registered-but-never-activated Serena charges the full tax for zero benefit — silently, and observed on the reference machine for two days (§7) — and that toggling it mid-session rewrites the frontmost bytes of the prefix and invalidates the **entire** cache (D50's mechanism). **Enable it at session start, not part-way through.** Use `/mcp` for refactor, test-writing, and architecture work on larger projects; leave it off for quick queries, small repos, and greenfield prototypes. The ~4×-on-cheap-lookups figure remains external and unverified (D53).

**Hard boundaries (enforced by the `claude-code` context, formerly `ide-assistant`):**

1. `execute_shell_command` is **disabled** by default in `claude-code` — keep it that way. Claude Code gates **Bash per command** and **MCP tools per tool**: a Bash rule can allow `git status` while still prompting for `rm`, whereas one approved `mcp__serena__execute_shell_command` is a blanket grant covering every command it will ever run. Enabling it would collapse per-command permission granularity into a single approval — a control regression, independent of compression. That, plus duplicate-tool routing confusion, is what the exclusion rests on (D3, D56). Until 3.0 it was justified by RTK bypass instead; RTK is gone and so is that reasoning (D51). The contract no longer *instructs* the agent to avoid the tool, because the tool is not in its surface to avoid (D56).
2. `read_file` / `search_for_pattern` are likewise disabled in `claude-code` — Claude Code provides those natively, and duplicate tools confuse routing.

These are structural, not instructional: the tools simply aren't in Serena's surface.

### 2.2 ponytail — minimal-code discipline (default-on)

**Answers:** nothing. ponytail routes no question and holds no state. It is a Claude Code plugin — a skill plus a SessionStart hook (`hooks/ponytail-instructions.js`) that generates a minimal-code-discipline ruleset and injects it into the session at startup.

**Mechanism:** instructions reaching the model, and nothing else. No process sits between Claude and the shell; no proxy sits between Claude Code and the API; nothing intercepts or transforms any data. The ruleset itself lives in the plugin and is deliberately **not** copied into [`contract.md`](contract.md) — one fact, one home (D30), and a local copy would drift from the plugin on its next release.

**Why it's in the stack (D54):** every layer 3.0 removed sat *in a path* — RTK rewrote commands before the shell, Headroom proxied the API, graphify maintained a derived artifact on disk — and each failed in a way that was a property of being in that path. ponytail is in no path. 3.0's throughline is that the stack **stops intercepting and starts instructing.**

**Node dependency:** the lifecycle hooks are Node.js, so `node` must be on the **non-interactive** shell's PATH — the trap for nvm and Nix users. Without it the skills still work and the always-on activation simply stays quiet rather than erroring on every prompt. A missing interpreter degrades the feature, never the session.

**Boundaries:** it is default-on because its cost is bounded (a small, stable text block that sits in the cached prefix) and its measured downside on lean tasks was zero rather than negative. That evidence is the vendor's and is not reproduced here (D54).

### 2.3 What the stack no longer owns

Two waste sources have **no owner** in 3.0, and saying so plainly is the point:

- **Tool-output noise** — RTK compressed it until 3.0. Nothing does now; keeping it small is a routing choice (§4 rule 5), not a layer.
- **Orientation** — graphify answered "what connects X to Y" until 3.0. Nothing does now; cold orientation is reading and searching again, and it is the most expensive thing the agent does. There is no successor and none is planned (D52).

Wire-level residue (`Read`-tool dumps, growing history) is likewise unowned (D51).

---

## 3. `[AGENT]` Routing matrix

Route every information need to exactly one layer. **Rows naming Serena apply only when Serena's tools are actually loaded** — when they are not, the native tool is not a fallback, it is the answer.

| Question shape | Route to | NOT to | Why |
|---|---|---|---|
| "Where is symbol S defined / who calls S?" | Serena (`find_symbol`, `find_referencing_symbols`) | grep | LSP is exact and current; grep has false positives |
| "What implements / uses this trait or type?" | Serena (`find_referencing_symbols`) | grep | Only the LSP resolves this correctly |
| "What's in this file?" (structure, not content) | Serena (`get_symbols_overview`) | reading the whole file | An overview costs a fraction of a full read |
| "Does this compile / what are the type errors?" | Serena (`get_diagnostics_for_file`) | running `cargo check` via Bash | Diagnostics are structured and already minimal |
| Editing a function/class body | Serena (`replace_symbol_body`, `insert_*_symbol`) | regex/string replace | Symbol-anchored edits don't hit comments, strings, or look-alike names |
| Renaming / refactoring a symbol | Serena symbol-level edits | search-and-replace | Avoids missed aliased imports and false hits |
| Any of the above, **Serena not enabled** | Claude Code's native Read/Grep/Glob/Edit | asking for Serena to be turned on | Off is the normal state, not a misconfiguration |
| Running tests / builds / linters / git / docker | Bash | — | Serena exposes no shell tool to route to (§2.1) |
| "How is this organized / what connects A to B?" | reading and searching, kept scoped | — | Unowned since 3.0 (§2.3, D52); no tool answers it |

**Tie-breakers:**

- Serena's tools **absent** → use native tools and move on. Do not ask for it to be enabled.
- Question names a **specific symbol** and Serena is on → Serena, always.
- Anything that **executes** → Bash.
- Orientation → scoped search. Budget it deliberately; nothing downstream will trim the result.

ponytail doesn't appear in this matrix because it never routes a question — it injects instructions and is invisible to routing (§2.2).

---

## 4. The routing contract `[AGENT]`

The global installer writes this contract into `~/.claude/CLAUDE.md` between sentinel markers, so re-running replaces it cleanly and touches nothing else. It is the authoritative, always-on instruction — there is no per-project copy.

The text itself is **not reproduced here**. It lives in [`contract.md`](contract.md) — the single file both installers read and `stack-init contract` prints — and the condensed form injected into agent files is [`contract-condensed.md`](contract-condensed.md). One copy is deliberate: a normative text quoted in three places drifts, and this one had already started to (the two installers disagreed on punctuation while claiming to write the same block).

The six rules in brief — 1 Serena is opt-in and usually off, so check before routing to it, 2 symbols → Serena when enabled, 3 diagnostics → Serena when enabled, 4 symbol-level edits → Serena when enabled, 5 anything that executes → Bash, 6 orientation has no owner. Source of truth: the LSP when enabled (§5).

Rule 1 is the **guard** the whole contract now hangs on. A global contract that ordered the agent to use tools which are usually not loaded would be wrong in most sessions, and the failure would be silent — the agent would either hallucinate the tools or treat their absence as breakage. Rule 1 makes "off" the documented normal state, which is what makes rules 2–4 safe to state unconditionally within it. This replaces 2.x's conditional rule 1, which guarded against a *graph* that might not exist yet (D52).

ponytail's minimal-code ruleset is **not** part of this contract — it is injected separately by the plugin's own hook (§2.2, D30, D54).

---

## 5. `[AGENT]` Source of truth

3.0 has only one source of derived knowledge about the code, so the tiered precedence spec earlier versions carried has nothing left to arbitrate (D52).

When Serena is enabled, the LSP is **ground truth by construction** — it is the compiler's live model, reflecting the working tree right now including uncommitted changes. It is never stale. Nothing else in the stack derives, indexes, or caches a second model of the code, so there is no second tier and no conflict rule.

When Serena is not enabled, the working tree read directly is the only source, with the ordinary caveat that a search result is evidence a string occurs, not evidence a symbol is used.

**What was removed and why it mattered:** until 3.0 the stack carried a precomputed graph whose whole epistemic risk was that it *trailed* the working tree, and §5 existed to say the LSP wins and the graph must be rebuilt. Removing graphify removes the staleness class entirely. That is a real simplification, not a bookkeeping one: the stack no longer has any way to be confidently wrong about code that has since changed.

---

## 6. Installation and operating model

3.0 is almost entirely *configuration*. The only per-repo **state** left is Serena's `.serena/project.yml`, and it costs no per-repo step — a global SessionStart hook writes and maintains it (§6.3). The graph, its refresh hooks, and every other derived artifact are gone (D52).

| | Global (once, ever) | Per-repo |
|---|---|---|
| Serena | MCP registration at **user scope**, left **disabled**; serena-autoinit SessionStart hook | `.serena/project.yml` + the activation note (autoinit, §6.3) |
| ponytail | marketplace + plugin install (§6.2) | — |
| Routing contract | `~/.claude/CLAUDE.md` (§4) | — |
| Language servers | rust-analyzer / ts-ls / pyright — once per language | — |

Serena's registration is deliberately *installed but not enabled* (D53): the config exists so `/mcp` can turn it on in one step for the sessions that want it, and costs nothing in the sessions that don't.

### 6.1 Global install — `stack-init` (no args)

Run once. The installer:

1. **Serena** — `uv tool install --from git+https://github.com/oraios/serena serena-agent`, then `claude mcp add --scope user serena -- serena start-mcp-server --context claude-code`, then **disables it** so it is off by default (D53). Three things about that command line are load-bearing:

   - **No `--project` flag** (D4). The registration is shared by every checkout, so it must be repo-agnostic. It does **not** follow that Serena finds the project itself — it is not cwd-aware and starts with no active project (§2.1, D33). Activation is a separate mechanism, installed by this same step: the **serena-autoinit SessionStart hook** (§6.3).
   - **`--context claude-code`** (the current name of the deprecated `ide-assistant`) is what disables the shell/read/search tools (§2.1, D3).
   - **A pinned binary, never `uvx --from git+…`** (D11) — a cold uv cache otherwise costs the session Serena entirely, and silently. The installer also migrates an existing uvx-based registration and sets `env.MCP_TIMEOUT = 120000` in `settings.json` as a safety net for a genuinely cold first launch (LSP download).
2. **ponytail** — see §6.2.
3. **Routing contract** — writes §4 into `~/.claude/CLAUDE.md` between sentinel markers (idempotent), injects the condensed form into `~/.claude/agents/*.md`, and registers the **contract-refresh SessionStart hook** (§6.x) that keeps those user-global copies in sync with `contract-condensed.md` without a re-install (D43).

Prereqs: `git`, `claude`, `node` (required — see §6.2); `uv` (for Serena); a language server per language.

### 6.2 ponytail — the plugin install

ponytail ships as a Claude Code plugin from a GitHub-backed marketplace. The `claude plugin` CLI drives both steps non-interactively, which is what lets the installer do it:

```
claude plugin marketplace add DietrichGebert/ponytail
claude plugin install ponytail@ponytail
```

Interactively the same thing is **two separate prompts** — `/plugin marketplace add DietrichGebert/ponytail`, then `/plugin install ponytail@ponytail`. Sending both in one message does not work. In the Desktop app's Code tab the same commands work in the prompt box, or via **+ → Plugins → Add plugin**, with marketplaces managed from **Customize** in the sidebar.

**`node` is a real prerequisite, with a soft failure.** The plugin's two lifecycle hooks are Node.js, so `node` must be on the **non-interactive** shell's PATH — not merely on an interactive one. This is the trap for nvm and Nix users, whose node often lives only in an interactive profile. If it is missing the skills still work; the always-on activation just stays quiet instead of erroring on every prompt. The installer checks for `node` and warns rather than aborting, matching D32 (an optional install never aborts the run).

Nothing else is per-repo, per-launch, or stateful: the plugin injects its ruleset at session start and touches nothing on disk (§2.2, D54).

### 6.3 Per-checkout Serena project — autoinit at session start

Serena's user-scope registration is repo-agnostic by design (§6.1 step 2), which leaves two gaps that have to be closed per checkout: the server has **no project config** and **no active project**. A global `SessionStart` hook (`~/.claude/hooks/serena-autoinit.sh` / `.ps1`, registered by `stack-init global`) closes both. Inside a git repo it:

1. **Derives the language-server set from tracked files** — `git ls-files`, mapped extension → server, with compiled/checked languages emitted first because the **first entry is Serena's default and fallback server**, so a real language must outrank `markdown`/`yaml`/`toml`.
2. **Writes `.serena/project.yml`** if there isn't one, carrying a `Generated by claude-context-stack (serena-autoinit)` header.
3. **Repairs a config it didn't write** — one produced by Serena's own auto-detection — but only when that file's `language_servers` list actually *misses* a language present in this checkout, and never destructively: the original is copied to `project.yml.bak-<timestamp>` and the `project_name` it was registered under is preserved, so an intentionally renamed project doesn't silently change identity.
4. **Leaves a marker-carrying file alone permanently**, so hand edits to a generated config survive every subsequent session.
5. **Excludes `.serena/` via `.git/info/exclude`** in the *common* git dir — never a tracked `.gitignore`. A background job must not mutate files the user would have to commit (D24), and one entry in the common dir covers the main checkout and every worktree.
6. **Always ends by emitting the activation instruction** — a SessionStart `additionalContext` naming the project and its path, and stating that Serena starts with no active project so `activate_project` must be called before the first symbol query and again whenever a tool answers "No active project". This fires on every path through the hook — wrote, repaired, or found a good config already there — because writing `project.yml` does not activate it.

Why the language set is derived rather than delegated to Serena's own detection, and why repair is gated on coverage rather than on the marker: D34. Why activation is a hook rather than a registration flag: D33.

**Worktrees.** A linked worktree gets its own project (`project_serena_folder_location` is `$projectDir/.serena`), named `repo@branch` so it stays distinguishable in the path-keyed registry and the dashboard. The main checkout gets `ignored_paths: [".claude/worktrees"]`, so worktrunk's nested worktrees don't return a near-duplicate hit per branch on every symbol lookup (D33).

**Operational caveat — the language-server set is fixed per session.** Serena binds a project's language servers when it first activates that project. Editing `project.yml` afterwards, or calling `activate_project` on it again *in the same session*, does **not** reload them; the tools keep answering with the old set until a brand-new session starts. Verify a repair by reading the file, not by re-running a Serena tool in the same session.

**Dashboard.** Serena runs one instance per Claude session, each on its own port, so its stock `web_dashboard_open_on_launch: true` means a browser tab per session. `stack-init global` sets that to `false` and then *pins* `web_dashboard_interface` rather than leaving it empty, because empty means "platform default" and a default can move. On Windows the pin is `tray_manager`. On Unix the installer probes for the two independent conditions a tray actually needs — a `org.kde.StatusNotifierWatcher` owner on the session bus, and a pystray backend that can reach it — injecting PyGObject into Serena's isolated `uv` tool venv first, since without it pystray silently binds its XEmbed backend and the icon is never drawn. Both true pins `tray_manager`; either false pins `browser`, leaving the dashboard reachable by asking Claude to open it or by visiting the port (D46).

**Opt-outs:** `CLAUDE_STACK_NO_SERENA_INIT=1` (global) or a `.serena-skip` file in the repo root (per repo). Uninstall by removing the `SessionStart` entry from `settings.json`.

### 6.4 Other subcommands

`stack-init verify` checks the wiring (Serena registered and **registered-but-disabled** as intended, serena-autoinit and contract-refresh hooks registered, ponytail marketplace added and plugin installed, `node` resolvable, contract present, and — in a repo — `.serena/project.yml` present; in a linked worktree it reports that the checkout carries its own Serena project over shared hooks). It cannot confirm the agent actually *activated* the Serena project, which is per-session; the autoinit hook's activation note (§6.3) covers that. Nor can it tell whether a given session chose to enable Serena at all — that is the point of D53, not a gap. Its repo-local checks resolve against `git rev-parse --show-toplevel`, not the current directory, so running it from a subdirectory (`config\`, as §6.5 suggests on Windows) reports the repo's real state. `stack-init contract` prints the routing contract for inspection; `stack-init contract --condensed` prints the short form injected into subagent files (§6.x). `stack-init verify --docs` checks this repo's own documentation rather than an installation: every `§` reference resolves to a real heading in this file, every `D<n>` citation resolves to an entry in `DECISIONS.md`. It is **Unix-only and deliberately not mirrored** in `stack-init.ps1` (D42) — it is a maintenance check for whoever edits the doc set, not something a user of the stack runs, and it is the one sanctioned exception to D2's equivalence rule, which still binds for everything that touches a user's machine. `stack-init help` (also `-h`/`--help`) prints the command list — on Windows this is load-bearing rather than a courtesy, because an unrecognised flag would otherwise be swallowed as a remaining argument and leave the default `global` command to run a full unattended install.

`stack-init init` and `stack-init stats` are **gone** in 3.0. `init` existed to build a repo's graph eagerly and there is no graph (D52); `stats` reported `rtk gain` and `headroom savings` and both tools are gone (D51, retiring D29).

### 6.5 Windows

`stack-init.ps1` is the Windows installer — the same `global` / `verify` / `contract` command surface and functional guarantees, equally idempotent. Platform-native integrations differ where necessary. Use PowerShell, not `cmd`: the contract write needs here-strings; batch would force `^`-escaping of every `|`/`>`/`<`/`&`. If a `cmd.exe` entry point is required, wrap it (`@powershell -ExecutionPolicy Bypass -File "%~dp0stack-init.ps1" %*`).

| Concept | Unix | Windows (PowerShell) |
|---|---|---|
| Claude config dir | `~/.claude/` | `$env:USERPROFILE\.claude\` |
| Routing contract | `~/.claude/CLAUDE.md` | `$env:USERPROFILE\.claude\CLAUDE.md` |
| Run the installer | `stack-init` | `.\stack-init.ps1` |

Notes: the SessionStart hooks are registered as `powershell -NoProfile …`, i.e. Windows PowerShell 5.1, whose `-Encoding utf8` prepends a BOM — so serena-autoinit writes `project.yml` through an explicit no-BOM encoder, keeping it byte-identical to the POSIX variant's output rather than relying on YAML parsers tolerating a BOM (§6.3). First run may need `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. Windows configures Serena's dashboard with `tray_manager` unconditionally, which Serena documents as fully supported there; the Unix installer reaches the same end state but has to *earn* it per desktop (D46). ponytail's `node` prerequisite (§6.2) is checked the same way on both platforms.

### 6.x Subagents

Task-tool subagents get a fresh context that does not load `~/.claude/CLAUDE.md`. The routing contract is prose injected into one specific file, so subagents never see it unless something puts it there. (Until 3.0 this section also noted that RTK's settings-level hook and Headroom's inherited env propagated automatically — both are gone, so the contract is now the *only* thing that needs propagating, and ponytail's SessionStart injection is a main-session mechanism.)

Mitigation (D19): `stack-init global` injects a condensed form of the contract into every `*.md` file under `~/.claude/agents/`, between the same kind of sentinel markers used for `CLAUDE.md` (idempotent — re-running replaces the block, doesn't duplicate it). If the directory has no agent files, the installer says so and does nothing. `stack-init contract --condensed` prints the same text for pasting into ad-hoc orchestrator prompts that spawn Task-tool subagents outside of a predefined agent file.

The user-global copies do not wait for the next install: a **contract-refresh SessionStart hook** re-injects `~/.claude/agents/*.md` at every session start, so editing `contract-condensed.md` propagates without re-running anything (D43). The hook stops there by design: `.claude/agents/` is tracked, and a background job never mutates files the user would have to commit (D24). The per-repo copies are now written only by `stack-init skills`-style explicit commands or by hand, and their staleness surfaces as a reviewable diff rather than silent drift.

---

## 7. Guardrails and known failure modes

**Serena assumed present when it is off (the 3.0 failure mode).** The contract routes symbol work to Serena, and Serena is usually not enabled (D53). An agent that treats the missing tools as breakage will either hallucinate them or stall asking for them to be turned on. Mitigation: contract rule 1 makes "off" the documented normal state and names the native tools as the answer, not a fallback (§4). The symptom is an agent saying it *cannot* look up a symbol; the correct behaviour is to Grep and move on.

**Serena registered but never activated (silent).** The highest-cost failure in the stack for sessions that *do* enable it, because nothing reports it. Serena is not cwd-aware and starts every session with no active project; if the session never calls `activate_project`, every symbol tool answers "No active project", the model falls back to grep, and contract rule 2 is unenforceable with no error surfaced. A near-miss variant is just as quiet: a `project.yml` written by Serena's own auto-detection can list a language set that omits most of the checkout, and the tools then answer `Cannot extract symbols … Active language servers: [...]` per file. Mitigation: the serena-autoinit hook (§6.3) writes/repairs the config and re-states the activation instruction at every session start, and contract rule 2 tells the agent to call `activate_project` rather than treating "No active project" as a reason to grep. Diagnosing it: check the session-start note names this checkout, read `.serena/project.yml` — and remember that a repair needs a **new session** to take effect (§6.3), so re-running a Serena tool in the same session is not a valid test.

**ponytail silently inert.** The plugin's hooks are Node.js. With no `node` on the **non-interactive** shell's PATH the always-on activation stays quiet — by design, so it doesn't error on every prompt — which means a broken install and a working one look identical from inside a session. Mitigation: `stack-init verify` checks `node` resolves and that the plugin is installed (`claude plugin list`). The symptom is the absence of the minimal-code ruleset in context; `claude plugin details ponytail` shows the component inventory and projected token cost, which is the direct check.

**Unowned waste, mistaken for a bug.** Orientation and tool-output noise have no owner (§2.3). An agent reading twenty files to orient, or a `cargo test` dumping thousands of tokens, is 3.0 working as specified — not a regression from 2.x. The mitigation is a routing choice: scope the search, prefer targeted commands. If that cost proves intolerable in practice, the answer is a new decision reversing D51/D52 on evidence, not a quietly reintroduced layer.

**Subagent contract bleed.** Task-tool subagents get fresh contexts that don't include `~/.claude/CLAUDE.md`, so spawned agents can grep where volume is highest. In 3.0 the contract is the *only* thing that propagates by injection, so this is the whole of the mitigation (§6.x, D19, D43).

**Hook integrity.** The stack owns two SessionStart hooks (serena-autoinit, contract-refresh) and no PreToolUse hook at all — RTK's was the only one and it is gone (D51). If another tool's installer rewrites the hooks array instead of merging, the stack's could be clobbered. After installing anything that touches `settings.json`, re-run `stack-init verify`.

---

## 8. Setup verification checklist

```bash
# Global
claude mcp list | grep -i serena             # registered, no --project arg
claude mcp list | grep -i serena             # ...and NOT enabled by default (D53)
claude plugin list | grep -i ponytail        # plugin installed
command -v node                              # required by ponytail's hooks (§6.2)
grep -q "Context routing" ~/.claude/CLAUDE.md  # contract present

# Per repo
cat .serena/project.yml                      # exists; language_servers covers this
                                             # checkout's languages, a real language first

# Behavior, in a Claude session
#  - default session: Serena's tools are ABSENT and the agent uses native
#    Read/Grep without asking for it to be enabled (contract rule 1)
#  - the minimal-code ruleset is present in context at session start (ponytail)
#  - session-start note names this checkout's Serena project + its path
#  - after `/mcp` enables Serena: "who calls <fn>" -> activate_project on that
#    path, then find_referencing_symbols; does NOT grep, and does NOT treat
#    "No active project" as a reason to grep
#  - get_diagnostics_for_file on a planted type error -> structured error, no dump
#  - agent tool list shows NO serena execute_shell_command / read_file
#    (structural: nothing in the contract needs to mention it, D56)
#  - an architecture question is answered by scoped reading/searching, and the
#    agent does NOT claim a graph tool is missing (unowned since 3.0, §2.3)

# Cost of the optional layer — MEASURED (D55), no longer an open follow-on
claude plugin details ponytail               # component inventory + projected token cost
#  Serena's manifest: 24 tools / 26,212 chars / 5,791 tokens under --context
#  claude-code; 30 tools / 8,299 tokens in Serena's default context. Reproduce by
#  driving an MCP tools/list handshake against `serena start-mcp-server` and
#  counting the serialised array with a real tokenizer (not chars/4).

# Serena retention gate (D57) - reported by `stack-init verify` on every run
grep -rl 'activate_project: .*session_id:' ~/.serena/logs/ | wc -l
#  0 after ~10 real sessions = Serena was never used; remove it AND stack-init
#  (B7). The "; session_id:" suffix is what separates a real call from the tool
#  name appearing in a startup manifest line.

# Editing the doc set (Unix only, D42)
stack-init verify --docs                     # every § and D<n> reference resolves
```

**No cache-economics benchmark.** 2.x carried one here — the procedure that would have settled whether Headroom was net-positive on effective cost (D37). It is gone with Headroom (D51). The question was ultimately answered without it: D49 and D50 measured the layer directly from its own proxy log, which is why the removal rests on evidence rather than on the matched-pair run nobody was ever going to do.

**What 3.0 gives up on measuring, honestly.** Nothing in this checklist proves the stack is cheaper than no stack. It proves the pieces are installed and the routing behaves. That is a deliberate retreat from 2.x's posture, which claimed savings it could not substantiate — and in Headroom's case was overstating them ~4× while every standing check read green (D51).

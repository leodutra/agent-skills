# Agent Code-Intelligence Stack — Operator's Manual

**Tools covered:** CodeGraph · Serena · Ponytail · native LSP
**Hosts covered:** Claude Code (primary) · Codex CLI · OpenCode
**Verified against:** repos, official docs, and independent benchmarks as of 2026-09-08. Anything marked *unverified* is stated as such.

---

## 0. The model behind every decision

Three layers, one cost function.

| Layer | Job | Tool |
|---|---|---|
| Retrieval | "Where is it, how does it connect" | CodeGraph |
| Edit | "Change exactly this symbol, everywhere" | Serena |
| Diagnostics | "Did that edit break the build" | Native LSP (Claude Code / OpenCode); Serena's LSP on Codex |
| Behavior | "Write less, reuse more" | Ponytail |

**Cost function:** `bill ≈ turns × resident context`. Every extra turn re-reads the whole window (cheap per token, but the whole window). Every extra resident token is paid again on every subsequent turn. Tokens *processed* and tokens *resident* are different numbers and both matter.

The three failure patterns that inflate turns, measured in independent A/B work:

1. **Lossy output** that triggers re-reads (the rtk finding: +13.8% turns, +7.6% cost, zero savings).
2. **Mid-task nudges** — reminders, warnings, redirects — the model reacts to.
3. **Address-only answers** (`file:line`) that force a follow-up Read.

Everything below is chosen to avoid all three: tools return complete, trusted answers or cost nothing per turn.

**Evidence quality, so you calibrate expectations:**

| Tool | Best evidence | Who ran it | Headline vs measured |
|---|---|---|---|
| CodeGraph | 7 repos × 1 question × median-of-4, CLI blocked in both arms | Vendor | 88% fewer tool calls per *question*; vendor also reports ~80% more residual context per session |
| Serena | Adoption only (~28k★) | — | Correctness is the language server's, not Serena's |
| Ponytail | 80 paired tasks, SkillsBench | JetBrains (independent) | Advertised −54% code / −22% tokens; measured −15% code, −10.3% cost (p=0.004), no quality diff |
| Native LSP | Vendor docs + community reports | — | No benchmark; mechanism is deterministic |

No head-to-head across tools exists. Measure your own sessions (§7).

---

## 1. Claude Code — cache rules that shape the install

Source: https://code.claude.com/docs/en/prompt-caching

- Requests are **append-only**. Hooks that inject `additionalContext` append; they don't bust the prefix. They do cost tokens every time they fire.
- **Tool definitions live in the system-prompt layer.** Changing the tool set between turns invalidates the cache. Built-in tool toggles and **permission rule edits** count.
- **MCP tools are deferred by default** (ToolSearch). A server connecting, disconnecting, or changing its tool list only appends — no invalidation. Cost: one ToolSearch round-trip the first time a tool is used per session.
- `CLAUDE.md` is delivered as a **user message after the system prompt**. Stable, cached, advisory. Re-assembled into every request, so it survives compaction.
- Documented invalidators: model switch, effort change, a bare-name tool deny, **compaction**, upgrade.
- Cache TTL: ~1 hour on subscription plans, 5 minutes on API billing.

**Operational consequences:**

- Pre-set all permissions in `settings.json` before the session. Never approve a tool prompt mid-session if you can avoid it.
- Decide the tool set (LSP plugins, MCP servers) at install time. Don't toggle mid-session.
- Compaction is the invalidator you control by habit: `/clear` between unrelated tasks; short scoped sessions.
- Don't change model or effort mid-session.

---

## 2. Claude Code — native LSP

### 2.1 What it is

A built-in `LSP` tool wired to language servers provided by **plugins**. Operations: `goToDefinition`, `findReferences`, `hover`, `documentSymbol`, `workspaceSymbol`, `goToImplementation`, `prepareCallHierarchy`, `incomingCalls`, `outgoingCalls`. Plus automatic diagnostics pushed into context after edits (`diagnostics: true` default). It does **not** do rename or symbol-body replacement — that stays Serena's job.

Reference: https://code.claude.com/docs/en/plugins-reference (LSP plugin section)

### 2.2 Activation path (the part people get wrong)

LSP servers are registered through the **plugin loader**, from `.lsp.json` in a plugin root or an `lspServers` block in `plugin.json`. A user-level `lspServers` key in `~/.claude/settings.json` has been observed to sit behind a feature gate and do nothing. Install via plugins.

**Official marketplace (TS, Python, and others):**

```
/plugin install typescript-lsp@claude-plugins-official
/plugin install pyright-lsp@claude-plugins-official
```

**Rust and the long tail — community marketplace (no patching required):**

```
/plugin marketplace add boostvolt/claude-code-lsps
/plugin install rust-analyzer@claude-code-lsps
/plugin install vtsls@claude-code-lsps      # alternative TS server
```

Note: `piebald-ai/claude-code-lsps` is a *different* marketplace that requires patching Claude Code with `tweakcc`. Prefer `boostvolt`.

**Offline / locked-down environments:** create a local marketplace with `strict: false` and the `lspServers` block inline. Documented pattern; same schema.

The language server binary must be on `PATH` (`typescript-language-server` + `typescript`; `rust-analyzer`). The official plugins auto-install theirs; verify with `which`.

### 2.3 Verify

```
claude --debug 2>&1 | grep "LSP MANAGER"
```

Pass criterion: `[LSP MANAGER] Starting async initialization` followed by `<server> initialized`. Then in-session: ask "go to definition of X" and confirm the response is labeled as an LSP call, not a Grep. If `[LSP MANAGER]` never appears and the session has no `LSP` tool, the feature is gated on your build; park it and re-test on the next Claude Code release.

Fallback diagnostic only (undocumented, community-discovered): `"env": {"ENABLE_LSP_TOOL": "1"}` in `settings.json`.

### 2.4 Gotchas

- Do **not** set `restartOnCrash` or `shutdownTimeout` on Claude Code < 2.1.205 — either option silently skipped the server at startup.
- All enabled servers start at session start and index immediately. JVM-based servers take ~8s; TS/Rust ~0.5–2s.
- Silent fallback is the real risk: a misconfigured server sends the model back to grep with no error. That's why you verify.
- The model defaults to Grep unless told otherwise. One CLAUDE.md line fixes this (§2.7).
- A plugin that is installed but *disabled* won't register its server. `claude plugin list` → status.

### 2.5 Turn accounting

Diagnostics-after-edit replaces a test-run turn: net negative. `findReferences` before a change replaces a grep-and-filter loop. Zero recurring token cost — built-in tool, already in the prefix.

---

## 3. Claude Code — CodeGraph

Repo: https://github.com/colbymchenry/codegraph · MIT · npm `@colbymchenry/codegraph`

### 3.1 What it is

Tree-sitter → SQLite (FTS5) knowledge graph. Native Rust kernel for 20 languages, portable engine for the rest. One MCP tool by default, `codegraph_explore`, returning verbatim source grouped by file + call paths + blast-radius summary. Native OS file watcher keeps the index fresh (2s debounce; ~0.3s resync on a 4k-file project). 100% local.

### 3.2 Install

```bash
# CLI (bundles its own runtime; no Node required)
curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh
# or: npm i -g @colbymchenry/codegraph

# Wire agents (global, once). Non-interactive:
codegraph install --target=claude --yes            # add codex,opencode as needed
# Per project:
cd your-project && codegraph init --yes
```

`codegraph install` writes: MCP server config, a marker-fenced instructions section (CLAUDE.md), and Claude Code allow rules. It does **not** index; `codegraph init` does.

**Pre-set permission (avoid the mid-session cache bust):**

```json
{ "permissions": { "allow": ["mcp__codegraph__*"] } }
```

### 3.3 MCP vs CLI — run both, MCP is primary

| | MCP (`codegraph serve --mcp`) | CLI (`codegraph explore`) |
|---|---|---|
| Watcher / freshness | Lives in this process. Staleness banner + connect-time catch-up | None. Stale unless MCP is running or you `codegraph sync` (a turn) |
| Model picks it | Typed tool, reliably chosen | Advisory via CLAUDE.md |
| Cache cost | One ToolSearch turn per session | Zero (Bash already in prefix) |
| Reaches subagents | No — MCP guidance only reaches the main agent | Yes — subagents read CLAUDE.md and have Bash |
| Unindexed project | Returns clean guidance to use built-in tools | Fails → a wasted turn |

The installer wires both. Keep both. The CLI section belongs in **`CLAUDE.local.md`** (per project, gitignored), not global — see the last row.

### 3.4 Where the config goes

| File | Contents | Scope |
|---|---|---|
| `~/.claude.json` / `settings.json` | MCP server entry, allow rule | User (never a client's repo) |
| `./CLAUDE.local.md` | The marker-fenced CodeGraph block; list of indexed packages in a monorepo | Per checkout, gitignored |
| `.gitignore` (global) | `.codegraph/` | Keeps the index out of client PRs |

Monorepos: `codegraph_explore` takes `projectPath`; index packages selectively and name them in the fence.

### 3.5 Turn and context accounting

- Vendor benchmark: 1–4 `explore` calls vs 28–43 grep/read, zero file reads on all seven repos. Single-question, headless, median of 4, CLI blocked in both arms — credible methodology, not a session number.
- **Residual context:** ~80% more retrieval context resident at end of session than a file-reading agent (vendor's own measurement; VS Code: 67k vs 18k). Mitigation is behavioral: name the file or symbol in the query so `explore` returns one body, not a subsystem; scope sessions; `/clear` between tasks.
- **Staleness banner** during the 2s debounce tells the agent to `Read` the file directly — +1 turn right after your own edits, bounded.
- **Native `Edit` requires a prior `Read`** in-session. `explore` returning source doesn't satisfy it. Edit with Serena (`replace_symbol_body`) after graph retrieval to stay turn-neutral; native `Edit` only for files Serena can't address.

### 3.6 Hygiene

- Pre-0.8 installers left `PostToolUse`/`Stop` hooks calling removed subcommands → the Stop hook failed every response. Re-run `codegraph install` to clean.
- WSL2 with the repo on `/mnt/*`: shared daemon socket is unreliable → `CODEGRAPH_NO_DAEMON=1` or move the tree to the Linux FS. Windows+WSL sharing one checkout: give each side its own `CODEGRAPH_DIR`.
- Network shares: WAL may not enable → reads block on writes. `codegraph status` shows `Journal:`.
- Telemetry is on by default: `codegraph telemetry off` or `DO_NOT_TRACK=1`.

---

## 4. Claude Code — Serena

Repo: https://github.com/oraios/serena · MIT core · JetBrains plugin is paid

### 4.1 What it is

LSP-over-MCP. Symbol-level retrieval (`find_symbol`, `find_referencing_symbols`, `get_symbols_overview`) and **symbol-level editing** (`rename_symbol`, `replace_symbol_body`, `insert_before/after_symbol`) backed by real language servers, 40+ languages. The edit tools are what nothing else in the stack provides.

### 4.2 Install

```bash
uv tool install -p 3.13 serena-agent
serena init
serena setup claude-code        # writes the MCP entry with --context claude-code
```

Manual entry equivalent: `claude mcp add -s user serena -- serena start-mcp-server --context claude-code`. Use `-s user` so nothing lands in a client repo's `.mcp.json`.

### 4.3 Trim the tool set — two phases

`~/.serena/serena_config.yml` → `fixed_tools` replaces the default set entirely (mutually exclusive with `excluded_tools` / `included_optional_tools`). One write.

**Phase 1 (now — native LSP not yet verified live):**

```yaml
fixed_tools:
  - find_symbol
  - find_referencing_symbols
  - get_symbols_overview
  - rename_symbol
  - replace_symbol_body
  - insert_after_symbol
  - insert_before_symbol
```

Drops: memory tools, onboarding, `think_about_*` (turns by design), file/shell utilities (Claude Code has its own). Symbol retrieval stays owned by Serena.

**Phase 2 (after §2.3 passes):** delete the first three lines. Serena's own tracker acknowledges they duplicate Claude Code's native LSP tool and recommends disabling them to save context. Serena becomes edit-only.

Also: disable the dashboard (`web_dashboard: false`), and pre-index large projects (`serena project index`) so the first symbolic call doesn't stall.

**Pre-set permission:** `mcp__serena__*` in `allow`.

### 4.4 Failure modes

- Thin language servers return no rename edits (zig, some others). The model then falls back to manual multi-file edits — the rtk failure shape. TS and Rust servers are solid.
- LSP spawn on first symbolic call: one-time latency, not per turn. Pre-index to hide it.
- `read_only: true` in `project.yml` is a safe first-run default if a client repo makes you nervous; enable write tools once you've seen it behave.

---

## 5. Claude Code — Ponytail

Repo: https://github.com/DietrichGebert/ponytail · MIT

### 5.1 What it is

A "lazy senior dev" decision ladder the agent climbs before writing code: does this need to exist → already in the codebase → stdlib/native does it → can it be one line. Validation, error handling that prevents data loss, security, and accessibility are explicitly excluded from simplification. Anything asked for explicitly is built in full.

Independent result (JetBrains, 80 paired tasks): −15% code, −10.3% cost, no measurable quality change. The saving only shows up where there was room to over-build.

### 5.2 Install — the plugin (the "purist" route)

```
/plugin marketplace add DietrichGebert/ponytail
/plugin install ponytail@ponytail
```

Restart. Node must be on the **non-interactive** PATH (nvm/Nix users: check), or activation is silently off while the commands still work.

What the plugin does on Claude Code, precisely:

| Hook | Fires | Does |
|---|---|---|
| `SessionStart` (`startup\|resume\|clear\|compact`) | Once per session, and after compaction | Injects the full ruleset as hidden context; writes mode flag |
| `SubagentStart` | Per subagent | Injects ruleset into the subagent |
| `UserPromptSubmit` | Every prompt | **Mode tracker only** — parses `/ponytail …`, emits nothing on ordinary prompts |

So there is **no per-turn ruleset injection on Claude Code** (that's the Qoder/OpenCode adapters). Recurring cost = six skill descriptions in the prefix + three Node spawns (latency). Injected ruleset sits in the same cached layer as CLAUDE.md.

### 5.3 Known costs and how to live with them

- **Mode is a global flag** (`$CLAUDE_CONFIG_DIR/.ponytail-active`). `/ponytail lite` in one repo applies everywhere until switched back. Put a reminder line in a client repo's `CLAUDE.local.md`: *"run `/ponytail lite` here"*.
- **Disabled ≠ off.** Open Claude Code bug: plugins set to `false` in `enabledPlugins` still fire SessionStart/UserPromptSubmit hooks. For an engagement that must have zero Ponytail, uninstall for that period.
- **`ponytail:` marker comments** are left in code as a debt ledger. Fine in your repos; in a client repo they're unexplained markers. Add one line to global `CLAUDE.md`: *"Do not emit `ponytail:` markers unless the project CLAUDE.md enables them."*
- **Don't also paste the ladder into CLAUDE.md.** One ruleset, the plugin's.
- **A/B contamination:** the SessionStart hook fires on any session, including headless baselines. If you benchmark the stack (§7), uninstall Ponytail for the control arm or the control arm isn't one.

### 5.4 Using the commands without paying for them

- `/ponytail-audit` — **never in a working session.** It reads the whole repo and returns a long report. `claude -p "/ponytail-audit" > audit.md`, or a dedicated session you `/clear` after. Once per project at onboarding.
- `/ponytail-review` — on the diff, before commit. One line per finding. This is the gate that catches what the ladder missed mid-session.
- `/ponytail` (full ruleset) — heavy build tasks with an over-build trap. Day-to-day, the always-on injection is enough.
- `/ponytail lite|full|ultra|off` — `lite` for unfamiliar house style (minimalism that fights conventions creates review churn); `ultra` in cleanup branches only.

### 5.5 The alternative, for the record

Instruction-only mode (rules file / `AGENTS.md`) is the author's supported second tier: zero hooks, zero spawns, per-project intensity by editing text, no commands. Skills can be copied standalone into `~/.claude/skills/` to get `/ponytail-review` and `/ponytail-audit` back without hooks. Smaller and cleaner; less faithful to upstream. Pick by how much you value running exactly what the author ships.

---

## 6. Claude Code — file layout and session hygiene

### 6.1 Which file gets what

| Goes in | File | Why |
|---|---|---|
| LSP-over-grep rule, Ponytail marker rule, Serena "prefer `replace_symbol_body` for symbol edits when available" | `~/.claude/CLAUDE.md` | Behavior travels with you; zero per-turn cost |
| CodeGraph CLI block; indexed packages; per-repo Ponytail intensity reminder; "Serena off here" if no server | `./CLAUDE.local.md` | Per checkout, gitignored, never in a client PR |
| Team conventions | `./CLAUDE.md` | Not your tooling |
| MCP servers | user scope (`-s user`) | Never a project `.mcp.json` in someone else's repo |
| `.codegraph/`, `.serena/` | global `.gitignore` | Same reason |

Global `CLAUDE.md` — keep it under ~30 lines. It's advisory; longer files get honored less. Suggested block:

```
## Code navigation
Use LSP for definitions, references, and diagnostics; Grep for non-code (configs, logs, strings).
When a .codegraph/ index exists, prefer codegraph_explore; trust its output, don't re-verify with grep.
For symbol-level edits use Serena's replace_symbol_body / rename_symbol when available; native Edit for non-code files.
Do not emit `ponytail:` marker comments unless the project CLAUDE.md enables them.
```

Never duplicate a rule across layers — every duplicate is paid every turn.

### 6.2 Session hygiene (worth more than any tool)

1. Permissions pre-set; no mid-session approvals.
2. Model and effort fixed for the session. Run at default-or-higher effort — low effort is where models burn turns reacting to tool output (rtk penalty vanished at high effort).
3. `/clear` between unrelated tasks. Compaction is the cache invalidator you control.
4. Stable server set. Don't enable/disable MCP servers or plugins mid-session.
5. Narrow retrieval queries. Name the symbol.
6. Graph for reading, Serena for writing.

### 6.3 What is deliberately not installed, and why

| Tool | Reason |
|---|---|
| Graphify | Independent A/B: quality tie, no session-level saving, agents kept grepping (46 vs 18). `--strict` mode adds a guaranteed extra turn by design. Only justified for repos inseparable from PDFs/diagrams. |
| GitNexus | PolyForm Noncommercial license (changed from MIT in 2026); 17 tools; PostToolUse "reindex" nudges; install friction. Capable, but gated by license for commercial work. |
| Graft | Push mode injects nodes per prompt via UserPromptSubmit. Pull mode is fine but then it's a second graph. Only tool with SWE-bench data (+12 pts on 50 instances) — swap in for TS-only repos where correctness outranks speed. Rust/C/C++/C# get name-resolved edges only. |
| rtk | Measured +7.6% cost, +13.8% turns. |
| Caveman | 8.5% output tokens; skill is harmless but a CLAUDE.md line does most of it. |
| Any second graph | Two maps of one repo → the agent picks the stale one. |

---

## 7. Verify and measure

### 7.1 Install checklist

```
[ ] claude --debug | grep "LSP MANAGER"          → server initialized (if LSP shipped)
[ ] codegraph status                             → index present, Journal: wal, no pending sync
[ ] codegraph_explore appears after first ToolSearch; allow rule pre-set
[ ] serena_config.yml fixed_tools = 7 (phase 1) / 4 (phase 2); dashboard off
[ ] /ponytail-help responds; node on non-interactive PATH; statusline optional
[ ] ~/.claude/CLAUDE.md < 30 lines; no rule duplicated in CLAUDE.local.md
[ ] .codegraph/ .serena/ in global gitignore; MCP servers user-scoped
[ ] No PreToolUse/PostToolUse/Stop hooks from any of these tools (codegraph install re-run if legacy)
```

### 7.2 Benchmark your own stack (the only number that's yours)

Paired, same task, same base commit, same model and effort, `claude -p`. Count **turns** and **cache reads** per task, not raw tokens — that's the metric that exposed rtk. Uninstall Ponytail for the control arm (its SessionStart hook fires regardless). Never trust k=1; per-task cost varies ~20% between identical runs. Match delegation shape (same subagent use) or you'll measure your workflow, not the tool.

---

## 8. Codex CLI

Codex has **no native LSP** as of the versions checked; the feature request is among the most upvoted open issues. Diagnostics come from Serena's language server or from running `tsc`/`cargo check` directly.

| Tool | Codex setup | Notes |
|---|---|---|
| **CodeGraph** | `codegraph install --target=codex --yes` → MCP entry in `~/.codex/config.toml` + `AGENTS.md` section pointing at `codegraph explore` | Same MCP tool, same CLI. Keep the `AGENTS.md` block per-project if you work in client repos. |
| **Serena** | `codex mcp add serena -- serena start-mcp-server --context codex` | `--context codex` exists and disables the overlapping file tools. `replace_regex` was removed from the codex context upstream — Codex's own edit tool is used for text edits. Keep phase-1 `fixed_tools` permanently here: nothing native takes over retrieval. |
| **Ponytail** | `codex plugin marketplace add DietrichGebert/ponytail` · `codex plugin add ponytail@ponytail` · in Codex run `/hooks`, trust its two lifecycle hooks, start a new thread | Same SessionStart + mode-tracker design as Claude Code. Instruction-only alternative: drop `AGENTS.md` in the repo or home dir. |
| **LSP** | None native | Document `tsc --noEmit` / `cargo check` in `AGENTS.md` as the post-edit check so the agent runs them itself. |

Codex hooks live in `~/.codex/hooks.json`, same schema as Claude Code. Any tool writing there is machine-wide; review with the tool's `--dry-run` / `--print-config` where offered.

---

## 9. OpenCode

OpenCode has **built-in LSP**, off by default, used for **diagnostics as feedback** (not a navigation tool the model calls). Its docs are candid that it "is not always a net positive" — servers get out of sync, use memory, and can slow the loop — and suggest documenting lint/typecheck commands in `AGENTS.md` instead where that's better.

| Tool | OpenCode setup | Notes |
|---|---|---|
| **LSP** | `opencode.json`: `{ "lsp": true }` to enable all built-ins, or an object to enable/override per server. Built-ins include TS/JS (`typescript`, `eslint`, `deno`), C/C++ (`clangd`), C#, Dart, Elixir, bash, and more; Rust via `rust-analyzer` if on `PATH` (verify in the current built-in table). `OPENCODE_DISABLE_LSP_DOWNLOAD=true` to stop auto-installs. | Diagnostics only. Enable it for TS/Rust and verify with `opencode debug lsp diagnostics <file>`. Known issue: ESLint diagnostics can time out at ~3s and return `{}`. |
| **CodeGraph** | `codegraph install --target=opencode --yes` → `~/.config/opencode/config.json` `mcp` entry (`"type": "local"`) | Same as elsewhere. |
| **Serena** | Documented OpenCode client; `mcp` local entry running `serena start-mcp-server` | Phase-1 `fixed_tools` permanently — OpenCode's LSP doesn't expose symbol tools to the model. |
| **Ponytail** | ES-module plugin that **appends the ruleset to the system prompt on every turn** via `experimental.chat.system.transform` | This is the one host where the plugin *is* per-turn. It lands in the system layer, so caching depends on how OpenCode assembles the prompt; assume it's re-sent. Prefer the instruction-only `AGENTS.md` route on OpenCode. |

---

## 10. Quick reference — per host

| | Claude Code | Codex | OpenCode |
|---|---|---|---|
| Retrieval | CodeGraph (MCP + CLI fence) | CodeGraph (MCP + AGENTS.md) | CodeGraph (MCP) |
| Symbol edits | Serena, 4 tools (after LSP) / 7 (before) | Serena, 7 tools | Serena, 7 tools |
| Diagnostics | Native LSP via plugins | `tsc`/`cargo check` in AGENTS.md | Built-in LSP, `lsp: true` |
| Behavior | Ponytail plugin | Ponytail plugin | Ponytail `AGENTS.md` (plugin is per-turn) |
| Per-turn hooks | None | None (Ponytail's are session/mode only) | None if instruction-only |
| Config scope | User + `CLAUDE.local.md` | User + `AGENTS.md` block | User + `AGENTS.md` |

---

## 11. Sources

- Claude Code prompt caching — https://code.claude.com/docs/en/prompt-caching
- Claude Code plugins reference (LSP) — https://code.claude.com/docs/en/plugins-reference
- CodeGraph — https://github.com/colbymchenry/codegraph
- Serena — https://github.com/oraios/serena · issue #858 (native LSP overlap)
- Ponytail — https://github.com/DietrichGebert/ponytail (`hooks/hooks.json`, `hooks/ponytail-activate.js`)
- JetBrains paired A/Bs: Caveman, rtk, Ponytail — https://blog.jetbrains.com/ai/2026/07/
- KubeNine Graphify vs grep — https://www.kubeblogs.com/graphify-vs-grep-claude-code-benchmark/
- OpenCode LSP — https://opencode.ai/docs/lsp/
- Codex LSP status — https://github.com/openai/codex/issues/8745
- Community LSP marketplace — https://github.com/boostvolt/claude-code-lsps

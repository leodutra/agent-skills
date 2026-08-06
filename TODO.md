# TODO — claude-context-stack ledger

Append-only ledger. Entries are never deleted or reworded once written; only the
status marker of a line changes as work progresses. New work is appended as a new
dated batch at the bottom.

## Status markers

| Marker | Meaning |
| --- | --- |
| `[ ]` | not started |
| `[~]` | in progress |
| `[x]` | change applied |
| `[v]` | applied **and** verified by running/observing it |
| `[-]` | deliberately not done (reason on the line) |
| `[!]` | blocked or failed (reason on the line) |

Every fix is a **paired edit**: the local `~/.claude` change *and* the matching change
in both `config/stack-init.ps1` and `config/stack-init.sh`, so a stack-init run
reproduces the fixed state on any machine or workspace. A line is only `[v]` when both
halves are done.

---

## 2026-08-05 — context stack audit (agent-skills)

Findings from auditing whether serena / graphify / rtk / headroom apply automatically
in every workspace. Instruction layer (global `CLAUDE.md` routing contract, global
`SessionStart` hooks, user-scope MCP, global skills) was found correct; the three
defects below are all in the plumbing.

### 1. Serena MCP times out at session start (silently voids the routing contract)

`uvx --from git+https://github.com/oraios/serena` rebuilds the package from git when
uv's cache is cold or the ref moves. Evidence — this session's log
`…\claude-cli-nodejs\Cache\C--workspaces-agent-skills\mcp-logs-serena\2026-08-05T21-40-50-559Z.jsonl`:
`Connection timeout triggered after 30089ms (limit: 30000ms)` preceded by
`Building serena-agent @ git+…`. No `mcp__serena__*` tools existed for the whole
session, so symbol lookups silently fell back to grep — exactly what contract rule 2
forbids. Connected fine (5.4 s) on 2026-08-02, i.e. intermittent and invisible.

- [v] 1.1 `uv tool install --from git+https://github.com/oraios/serena serena` (persistent binary, no build at launch) — real package name is `serena-agent`; installed 3 executables to `~/.local/bin` (`serena`, `serena-agent`, `serena-hooks`), `serena --version` = 1.6.2.dev0 in 5.5 s with no git build
- [v] 1.2 Re-register user scope: `claude mcp add --scope user serena -- serena start-mcp-server --context ide-assistant` — registered as `serena start-mcp-server --context claude-code` (see 1.7)
- [v] 1.3 Add `env.MCP_TIMEOUT` safety net to `~/.claude/settings.json` — set to `"120000"`; takes effect next session, so confirmed by 1.6
- [x] 1.4 Mirror 1.1–1.3 in `config/stack-init.ps1` — new `Set-GlobalEnvVar`; serena block now installs the binary, migrates any `uvx`-based registration, registers `claude-code`, sets `MCP_TIMEOUT`; one shared `claude mcp list` pass. Parse-checked; the `install_global` path itself was not executed.
- [x] 1.5 Mirror 1.1–1.3 in `config/stack-init.sh` — same, via new `set_global_env_var`. `bash -n` clean; not executed.
- [v] 1.6 Verify: fresh session exposes `mcp__serena__*` tools — confirmed in a fresh session on 2026-08-05 (see batch below)
- [v] 1.7 Appended during 1.2 — switched `--context ide-assistant` to `--context claude-code`; Serena's own log says `Context name 'ide-assistant' is deprecated and has been renamed to 'claude-code'`. Same toolset (24 exposed tools, shell/read tools excluded). Still to mirror in 1.4/1.5.

### 2. Stray broken `headroom` MCP registration

`headroom mcp serve` crashes on startup on every session since 2026-08-02
(`AttributeError: 'Server' object has no attribute 'list_tools'` →
`Connection failed (-32000): Connection closed`). `stack-init` never registers it —
headroom's real integration is the wire proxy via the `claude` shim, which is healthy
(`ANTHROPIC_BASE_URL=http://127.0.0.1:8787`, `CLAUDE_STACK_SHIM=1`). The entry is a
hand-added user-scope server costing ~2.7 s of startup in every workspace for nothing.

- [v] 2.1 `claude mcp remove --scope user headroom` — removed from user config
- [x] 2.2 Teach `config/stack-init.ps1` to drop a stray `headroom` MCP registration — added to the Headroom step, reusing the shared `claude mcp list` pass. Parse-checked; not executed.
- [x] 2.3 Teach `config/stack-init.sh` to drop a stray `headroom` MCP registration — same. `bash -n` clean; not executed.
- [v] 2.4 Verify: `claude mcp list` shows no `headroom` entry — confirmed; the full health check now takes 9.4 s and serena reports `✔ Connected`

### 3. RTK hook does not cover the `PowerShell` tool

The `PreToolUse` hook matcher is `"Bash"` only (`rtk init -g`, stack-init.ps1:475). On
Windows the `PowerShell` tool is a separate tool name and bypasses RTK entirely, so its
output reaches the model uncompressed. Contract rule 5 ("anything that executes → Bash")
mitigates this by instruction only, with nothing enforcing it.

- [-] 3.1 Extend the RTK `PreToolUse` matcher to cover `PowerShell` in `~/.claude/settings.json` — not done. RTK's rewriter targets POSIX command lines; pointing it at PowerShell risks mangling cmdlet pipelines (`cat foo | Select-String bar`). The probe that would have settled this was declined, so widening the matcher globally without evidence was the wrong trade. Superseded by 3.5–3.8.
- [-] 3.2 Mirror in `config/stack-init.ps1` — moot, see 3.1
- [-] 3.3 Mirror in `config/stack-init.sh` — moot, see 3.1
- [-] 3.4 Verify: a `PowerShell` call is routed through `rtk hook claude` — moot, see 3.1
- [x] 3.5 Instead: contract rule 5 now names the `PowerShell` tool as an RTK bypass, in `~/.claude/CLAUDE.md` (managed block), both stack-init contract heredocs (full + condensed), and `config/claude-code-context-stack.md` §4
- [x] 3.6 `claude-code-context-stack.md` known-gaps entry "Shell routing around RTK" now states the matcher is `Bash`-only and that the PowerShell mitigation is instructional, not structural
- [x] 3.7 Same doc: decision-table row for tests/builds/git now lists the PowerShell tool as an avoid-on-Windows
- [ ] 3.8 Open question left for later: whether RTK can safely handle PowerShell input at all (needs the declined probe, or a look at RTK's rewriter source)

### 4. Noted, not scheduled

- [x] 4.0 Doc sync (appended): `config/claude-code-context-stack.md` updated for the `ide-assistant` → `claude-code` context rename (§2.2 boundaries, §installer step 2, §decisions) and for the pinned-binary/`MCP_TIMEOUT` rationale
- [ ] 4.2 Found by `stack-init verify` during this batch, unrelated to 1–3: this repo reports `graph refresh: MISSING (checkout/merge/rewrite)` — the post-checkout/post-merge/post-rewrite git hooks were never installed here (post-commit is present). Not fixed; needs a decision on whether to backfill via `stack-init init`.
- [-] 4.1 Headroom selfheal hook + `ANTHROPIC_BASE_URL` pin live in this repo's `.claude/settings.local.json`, not globally — written by headroom itself per-project; the global shim already wraps every workspace, so no action.

---

## 2026-08-05 — post-restart verification (agent-skills)

Closes 1.6, the one open verification from the batch above. Observed in a fresh
session, i.e. the first session started after the batch's `~/.claude` changes.

- [v] 5.1 Serena tools present: 22 `mcp__serena__*` tools exposed (`find_symbol`, `find_referencing_symbols`, `get_symbols_overview`, `get_diagnostics_for_file`, `replace_symbol_body`, `rename_symbol`, …), so contract rules 2–4 are enforceable again
- [v] 5.2 `claude mcp list` → `serena: serena start-mcp-server --context claude-code - ✔ Connected`; launches from the pinned binary, no `uvx`, no git build
- [v] 5.3 `serena` on PATH at `~/.local/bin/serena`, version 1.6.2.dev0 — matches 1.1
- [v] 5.4 No `headroom` entry in `claude mcp list`; wire proxy healthy in this session (`ANTHROPIC_BASE_URL=http://127.0.0.1:8787`, `CLAUDE_STACK_SHIM=1`, shims present in `~/.claude/stack-bin`) — 2.1/2.4 hold across a restart
- [v] 5.5 `env.MCP_TIMEOUT` present in `~/.claude/settings.json`; this session connected under it (closes 1.3)
- [v] 5.6 `config/stack-init.sh` mirror re-checked against the `.ps1`: `uv tool install … serena-agent`, `uvx` migration, `--context claude-code`, `set_global_env_var MCP_TIMEOUT 120000`, stray-`headroom` removal all present; `bash -n` clean
- [-] 5.7 Execute `stack-init install_global` end-to-end to lift 1.4/1.5/2.2/2.3 from `[x]` to `[v]` — not done; it rewrites global `~/.claude` state, which is beyond a verification pass. The code paths are parse-checked only, so those four lines stay `[x]`.
- [ ] 5.8 `graphifyy[all]` (double-y) confirmed as the intended PyPI name, not a typo — pre-existing, documented in `claude-code-context-stack.md` §installer step 3. Noted only, no action.

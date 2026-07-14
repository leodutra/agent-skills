#!/usr/bin/env bash
# =============================================================================
#  Claude Code Context Stack  —  global installer + per-repo init  (Linux/macOS)
# =============================================================================
#
#  WHAT THIS IS
#  Four tools that cut the token cost of working in a real codebase with Claude
#  Code, plus the routing rules that make Claude actually use them. Nothing else
#  — no spec/ADR/worklog layer. Each tool kills one source of wasted context:
#
#    graphify  structure   one-time codebase graph (tree-sitter, local).
#                          Kills ORIENTATION cost — answers "what connects X to
#                          Y / blast radius / how is this organized" without the
#                          agent reading dozens of files to find out.
#    Serena    symbols     LSP over MCP (rust-analyzer / tsserver / pyright).
#                          Kills RETRIEVAL+EDIT cost — exact symbol defs, refs,
#                          implementations, diagnostics, and symbol-level edits
#                          instead of whole-file dumps and grep walls.
#    RTK       output      Bash PreToolUse hook that compresses command output
#                          60-90% before it reaches the window. Kills TOOL-OUTPUT
#                          noise (cargo test ~92%, git status ~81%). Invisible.
#    Headroom  wire        Local proxy (`headroom wrap claude`) that recompresses
#                          whatever still reaches the API after the three layers
#                          above — file dumps, growing history. Second pass, not
#                          a replacement for any of them.
#
#  DESIGN PRINCIPLE: one question per layer, no layer answers another's.
#    architecture/cross-module -> graphify   |   specific symbols -> Serena
#    compile/type diagnostics   -> Serena     |   execute anything -> Bash (RTK)
#    everything left over at the wire -> Headroom (catch-all, not a router)
#  PRECEDENCE on conflict: LSP (Serena, live ground truth) > graph (can be stale).
#
#  WHAT IS GLOBAL vs PER-REPO
#    Global (run once): RTK hook, Serena at user scope (auto-activates per repo
#      from cwd), graphify install, Headroom install, and the routing contract
#      in ~/.claude/CLAUDE.md.
#    Per-repo (one command): the graph is a derivation of a specific codebase, so
#      `stack-init init` builds it and installs a local post-commit rebuild hook.
#      Repos without a graph still work — the contract degrades gracefully.
#
#  USAGE
#    stack-init            # or: stack-init global    -> global install (once)
#    stack-init init       # inside a repo            -> build graph + hooks
#    stack-init verify     # check everything is wired
#    stack-init contract   # print the routing contract it installs
#    stack-init contract --condensed  # print the short form injected into agents
#    stack-init stats      # append + print a usage snapshot (rtk/headroom)
#
#  AFTER GLOBAL INSTALL: start sessions with `headroom wrap claude`, not a bare
#  `claude`, or Headroom's compression never engages (RTK/Serena/graphify wire
#  into the session itself, so they're unaffected either way).
#
#  PREREQS: cargo, pip, uv, claude (Claude Code CLI), git. A language server per
#  language (rust-analyzer via `rustup component add rust-analyzer`, etc.).
# =============================================================================
set -euo pipefail

CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
CLAUDE_MD="$CLAUDE_DIR/CLAUDE.md"
B='\033[1;32m'; Y='\033[1;33m'; R='\033[1;31m'; N='\033[0m'
say()  { printf "${B}==>${N} %s\n" "$*"; }
warn() { printf "${Y}warn:${N} %s\n" "$*"; }
err()  { printf "${R}error:${N} %s\n" "$*" >&2; }
have() { command -v "$1" >/dev/null 2>&1; }

print_contract() {
cat <<'BLOCK'
# >>> claude-context-stack >>> (managed by stack-init — edits here are overwritten)
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
   insert_after_symbol, rename_symbol), not string/regex replacement.
5. Anything that executes (tests, builds, git, tooling) -> Bash. RTK compresses it.
   Do NOT route execution through any MCP shell tool — that bypasses RTK.
6. The graph reflects the last REBUILD (normally the last commit).
   - Symbol-level questions about uncommitted work -> Serena (live). Never the graph.
   - ARCHITECTURAL questions that involve uncommitted work -> run `graphify update .`
     first (incremental, content-hash cached, cheap), then query the graph as normal.

## Source-of-truth precedence (on conflict)
code/LSP (Serena)  >  graph (graphify)
The LSP is live ground truth; the graph is a derivation that can trail the working
tree. On conflict, trust the LSP and rebuild the graph (`graphify update .`).
# <<< claude-context-stack <<<
BLOCK
}

print_contract_condensed() {
cat <<'BLOCK'
# >>> claude-context-stack >>> (condensed, managed by stack-init — edits here are overwritten)
1. Architecture/cross-module -> graphify (graphify-out/GRAPH_REPORT.md, `graphify query`/`path`). Never grep/read-many for this.
2. Specific symbols -> Serena (find_symbol, find_referencing_symbols, get_symbols_overview). Never grep for symbol names.
5. Anything that executes -> Bash (RTK compresses it). Never an MCP shell tool.
6. Graph = last REBUILD. Uncommitted+symbol -> Serena. Uncommitted+architectural -> `graphify update .` first, then query.
Precedence on conflict: code/LSP (Serena) > graph (graphify).
# <<< claude-context-stack <<<
BLOCK
}

inject_condensed_contract() {
  local dir="$1" f found=0
  if [ ! -d "$dir" ]; then
    say "  no agent files at $dir — skipping condensed contract injection"
    return
  fi
  for f in "$dir"/*.md; do
    [ -e "$f" ] || continue
    found=1
    if grep -q '>>> claude-context-stack >>>' "$f"; then
      local tmp; tmp="$(mktemp)"
      awk '/>>> claude-context-stack >>>/{s=1} !s{print} /<<< claude-context-stack <<</{s=0}' \
        "$f" > "$tmp" && mv "$tmp" "$f"
    fi
    print_contract_condensed >> "$f"
  done
  if [ "$found" = 1 ]; then say "  condensed contract injected into $dir/*.md"
  else say "  no agent files at $dir — skipping condensed contract injection"; fi
}

check_deps() {
  local miss=0
  for d in git claude; do have "$d" || { err "missing required: $d"; miss=1; }; done
  have cargo || warn "cargo not found — needed to install RTK (Arch: pacman -S rust / rustup)"
  have pip   || warn "pip not found — needed to install graphify"
  [ "$miss" = 0 ] || { err "install the required tools above, then re-run"; exit 1; }
}

write_git_hook() {
  # Merge-not-clobber: skip if our marker is already there, append under the
  # marker if some other tool owns the file, otherwise create it fresh.
  local name="$1" body="$2"
  local path=".git/hooks/$name"
  if [ -f "$path" ] && grep -q 'claude-context-stack:' "$path" 2>/dev/null; then
    return
  fi
  if [ -f "$path" ]; then printf '\n%s\n' "$body" >> "$path"
  else printf '#!/bin/sh\n%s\n' "$body" > "$path"; fi
  chmod +x "$path"
}

install_refresh_hooks() {
  write_git_hook post-checkout '# claude-context-stack: refresh graph on branch switch (not file checkout)
if [ "$3" = "1" ] && command -v graphify >/dev/null 2>&1 && [ -d graphify-out ]; then
  ( graphify update . >/dev/null 2>&1 & )
fi'
  write_git_hook post-merge '# claude-context-stack: refresh graph after merge/pull
command -v graphify >/dev/null 2>&1 && [ -d graphify-out ] && graphify update . >/dev/null 2>&1 || true'
  write_git_hook post-rewrite '# claude-context-stack: refresh graph after rebase
command -v graphify >/dev/null 2>&1 && [ -d graphify-out ] && graphify update . >/dev/null 2>&1 || true'
}

install_uv() {
  have uv && return
  say "  installing uv (needed to run Serena)"
  if have pacman; then sudo pacman -S --noconfirm uv
  else curl -LsSf https://astral.sh/uv/install.sh | sh; fi
  have uv || warn "uv install failed — Serena will not be able to launch"
}

install_headroom_check() {
  mkdir -p "$CLAUDE_DIR/hooks"
  cat > "$CLAUDE_DIR/hooks/headroom-check.sh" <<'HOOK'
#!/usr/bin/env bash
# claude-context-stack: detect a bare (unwrapped) Claude Code launch
url="${ANTHROPIC_BASE_URL:-}"
case "$url" in
  *127.0.0.1*|*localhost*) exit 0 ;;
esac
printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"NOTE: Headroom proxy not active this session (bare launch). Wire-level compression off; RTK/Serena/graphify unaffected."}}'
exit 0
HOOK
  chmod +x "$CLAUDE_DIR/hooks/headroom-check.sh"

  local settings="$CLAUDE_DIR/settings.json" merge_py result
  mkdir -p "$CLAUDE_DIR"; [ -f "$settings" ] || echo '{}' > "$settings"
  merge_py="$(mktemp)"
  cat > "$merge_py" <<'PYEOF'
import json, sys
path, hook_cmd = sys.argv[1], sys.argv[2]
try:
    with open(path) as f:
        data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    data = {}
hooks = data.setdefault('hooks', {})
starts = hooks.setdefault('SessionStart', [])
if not any(h.get('command') == hook_cmd for entry in starts for h in entry.get('hooks', [])):
    starts.append({'hooks': [{'type': 'command', 'command': hook_cmd}]})
with open(path, 'w') as f:
    json.dump(data, f, indent=2)
rtk_present = any('rtk' in str(h) for h in hooks.get('PreToolUse', []))
print('rtk-hook-present' if rtk_present else 'rtk-hook-missing')
PYEOF
  result="$(python3 "$merge_py" "$settings" "bash \"$CLAUDE_DIR/hooks/headroom-check.sh\"" 2>&1)"
  rm -f "$merge_py"
  if [ "$result" = "rtk-hook-present" ]; then
    say "  SessionStart headroom-check hook installed; RTK PreToolUse hook still present"
  else
    warn "settings.json written but RTK's Bash hook wasn't found afterward ($result) — check $settings manually"
  fi
}

install_global() {
  check_deps
  say "RTK — output compression (global Bash hook)"
  if have rtk; then say "  rtk present ($(rtk --version 2>/dev/null))"
  else say "  installing rtk"; cargo install --git https://github.com/rtk-ai/rtk; fi
  rtk init -g && say "  rtk init -g (PreToolUse Bash hook registered)"

  say "Serena — LSP symbols over MCP (user scope, auto-activates per repo)"
  if claude mcp list 2>/dev/null | grep -qi '^serena\|serena '; then
    say "  serena already registered — skipped"
  else
    install_uv
    claude mcp add --scope user serena -- uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context ide-assistant
    say "  serena registered at user scope (--context ide-assistant: no shell/read tools)"
  fi

  say "graphify — codebase knowledge graph"
  if ! have graphify; then
    say "  installing graphify (PyPI package: graphifyy, double-y)"
    if have uv; then uv tool install 'graphifyy[all]'; else pip install 'graphifyy[all]'; fi
  fi
  graphify install >/dev/null 2>&1 && say "  /graphify skill installed (global)"
  # Deliberately NOT running `graphify claude install` here: it targets the
  # CLAUDE.md / .claude/settings.json in the CURRENT DIRECTORY, not this
  # script's global $CLAUDE_MD - wrong layer for a global install step. Its
  # PreToolUse Bash/Read/Glob hook also fires unconditionally on every
  # matching call (confirmed active, not a no-op) - noisier than contract
  # rule 1 below, which scopes graphify to architecture questions only. Wire
  # this into init_project instead if per-repo defense-in-depth is wanted.

  say "Headroom — proxy-layer compression (final pass before the API)"
  if have headroom; then say "  headroom present ($(headroom --version 2>/dev/null))"
  else
    say "  installing headroom (PyPI package: headroom-ai)"
    if have uv; then uv tool install 'headroom-ai[all]'; else pip install 'headroom-ai[all]'; fi
  fi
  say "  installed — writing a launcher wrapper (never aliasing 'claude' itself,"
  say "  which risks self-recursion when headroom resolves the target binary)"
  WRAPPER_NAME=""
  for candidate in clw hclaude claudew; do
    if ! have "$candidate"; then WRAPPER_NAME="$candidate"; break; fi
  done
  if [ -z "$WRAPPER_NAME" ]; then
    warn "clw/hclaude/claudew all taken — skipping wrapper; launch via 'headroom wrap claude' manually"
  else
    mkdir -p "$HOME/.local/bin"
    printf '#!/usr/bin/env bash\nexec headroom wrap claude "$@"\n' > "$HOME/.local/bin/$WRAPPER_NAME"
    chmod +x "$HOME/.local/bin/$WRAPPER_NAME"
    say "  wrapper installed: $WRAPPER_NAME (launch sessions with '$WRAPPER_NAME')"
    case ":$PATH:" in *":$HOME/.local/bin:"*) ;; *) warn "$HOME/.local/bin not on PATH — add it to use '$WRAPPER_NAME'" ;; esac
  fi
  install_headroom_check
  # Deliberately not passing --code-graph (would build a second structure graph,
  # duplicating graphify - rule 1 below already owns that question) or --memory
  # (this stack manages no intent/memory layer by design, see decisions log).

  say "opensrc — dependency source fetcher (context tool, OUTSIDE the routing contract)"
  # Also not a routing layer: it answers one question the four tools can't —
  # "what does this dependency actually do" — by fetching the exact installed
  # version's source into a global cache (~/.opensrc, shared by all checkouts
  # and worktrees; zero per-repo state). Usage guidance lives in the opensrc
  # skill, not the contract. Non-fatal like every extra below.
  if have opensrc; then say "  opensrc present"
  elif have npm; then
    npm install -g opensrc && say "  opensrc installed (npm -g)" \
      || warn "npm install -g opensrc failed — install later, stack unaffected"
  else warn "npm not found — skipping opensrc (npm install -g opensrc later)"
  fi

  say "worktrunk — parallel worktrees (workflow tool, OUTSIDE the routing contract)"
  # Not a token layer and deliberately absent from the contract below — it routes
  # nothing. It manages worktree lifecycle so parallel agents/tasks each get their
  # own checkout. One rule makes worktrees indistinguishable from any checkout:
  # the global post-start hook below re-runs the stack's per-checkout init
  # (graphify graph + rebuild hook) in every new worktree, but only for repos
  # whose primary checkout opted in (graphify-out/ exists). Every step here is
  # non-fatal: a worktrunk failure must never block the token stack.
  if have wt || have git-wt; then say "  worktrunk present"
  else
    say "  installing worktrunk"
    if have brew; then brew install worktrunk || warn "brew install worktrunk failed"
    else cargo install worktrunk || warn "cargo install worktrunk failed"; fi
  fi
  WT_BIN="$(command -v wt || command -v git-wt || true)"
  if [ -n "$WT_BIN" ]; then
    "$WT_BIN" config shell install \
      || warn "shell integration failed — run '$WT_BIN config shell install' manually"
    WT_CFG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/worktrunk"
    WT_CFG="$WT_CFG_DIR/config.toml"
    mkdir -p "$WT_CFG_DIR"; touch "$WT_CFG"
    if grep -q 'claude-context-stack' "$WT_CFG"; then
      say "  post-start hook already present — skipped"
    elif grep -Eq '^[[:space:]]*(\[\[?post-start|post-start[[:space:]]*=)' "$WT_CFG"; then
      # Appending a second [post-start] table would make the whole TOML invalid
      # and break worktrunk entirely — never do it. Ask for a manual merge.
      warn "config.toml already defines post-start — add this line to it manually:"
      warn "claude-context-stack = \"[ -d '{{ primary_worktree_path }}/graphify-out' ] && graphify . && graphify hook install || true\""
    else
      cat >> "$WT_CFG" <<'WTHOOK'

# claude-context-stack: replicate the stack's per-checkout state (graphify graph
# + post-commit rebuild hook) into every new worktree, only where the primary
# checkout was stack-inited. Delete this block to opt out.
[post-start]
claude-context-stack = "[ -d '{{ primary_worktree_path }}/graphify-out' ] && graphify . && graphify hook install || true"
WTHOOK
      say "  global post-start hook written -> $WT_CFG"
    fi
  else
    warn "worktrunk unavailable — parallel-worktree support skipped (stack unaffected)"
  fi

  say "Routing contract -> $CLAUDE_MD"
  mkdir -p "$CLAUDE_DIR"; touch "$CLAUDE_MD"
  if grep -q '>>> claude-context-stack >>>' "$CLAUDE_MD"; then
    local tmp; tmp="$(mktemp)"
    awk '/>>> claude-context-stack >>>/{s=1} !s{print} /<<< claude-context-stack <<</{s=0}' \
      "$CLAUDE_MD" > "$tmp" && mv "$tmp" "$CLAUDE_MD"
    say "  refreshed existing managed block"
  fi
  print_contract >> "$CLAUDE_MD"
  say "  contract written (idempotent — re-running replaces the managed block)"

  say "Condensed contract -> subagent files (~/.claude/agents/)"
  inject_condensed_contract "$CLAUDE_DIR/agents"

  have rust-analyzer || warn "rust-analyzer not on PATH — Serena needs it for Rust (rustup component add rust-analyzer)"
  echo; say "Global install done. In each repo, run:  $(basename "$0") init"
}

init_project() {
  [ -d .git ] || { err "run from a git repo root (no .git here)"; exit 1; }
  have graphify || { err "graphify not installed — run '$(basename "$0") global' first"; exit 1; }
  say "building knowledge graph (graphify .)"; graphify .
  say "installing local post-commit hook (incremental rebuild)"; graphify hook install
  say "installing post-checkout/post-merge/post-rewrite refresh hooks"; install_refresh_hooks
  if ! { [ -f .gitignore ] && grep -q '^graphify-out/' .gitignore; }; then
    printf '\n# Claude context-stack knowledge graph\ngraphify-out/\n' >> .gitignore
    say "gitignored graphify-out/"
  fi
  say "Condensed contract -> subagent files (.claude/agents/)"
  inject_condensed_contract ".claude/agents"
  echo; say "Repo ready. First Claude session: let Serena onboard, then ask one"
  say "architecture question and confirm it reads the graph instead of grepping."
}

stats() {
  local dir="$CLAUDE_DIR/stack-stats" ts snap rtk_out headroom_out
  mkdir -p "$dir"
  ts="$(date -u +%Y%m%dT%H%M%SZ)"
  snap="$dir/$ts.json"
  if have rtk; then rtk_out="$(rtk gain 2>&1 || true)"; else rtk_out="rtk not on PATH"; fi
  if have headroom; then headroom_out="$(headroom stats 2>&1 || true)"; else headroom_out="headroom not installed"; fi
  python3 - "$snap" "$ts" "$rtk_out" "$headroom_out" <<'PYEOF'
import json, sys
path, ts, rtk_out, headroom_out = sys.argv[1:5]
with open(path, 'w') as f:
    json.dump({'date': ts, 'rtk_gain': rtk_out, 'headroom_stats': headroom_out}, f, indent=2)
PYEOF
  say "  snapshot written -> $snap"
  local snaps
  snaps="$(ls -1 "$dir"/*.json 2>/dev/null | sort | tail -2)"
  [ -z "$snaps" ] && return
  say "  last two snapshots:"
  echo "$snaps" | while IFS= read -r f; do
    echo "--- $f ---"; cat "$f"
  done
}

verify() {
  say "verifying"
  have rtk && echo "  rtk:            OK ($(rtk --version 2>/dev/null))" || echo "  rtk:            NOT ON PATH"
  rtk gain >/dev/null 2>&1 && echo "  rtk hook:       active" || echo "  rtk hook:       no stats yet (run a few Bash cmds)"
  claude mcp list 2>/dev/null | grep -qi serena && echo "  serena (mcp):   OK (user scope)" || echo "  serena (mcp):   NOT registered"
  have graphify && echo "  graphify:       OK" || echo "  graphify:       NOT installed"
  have headroom && echo "  headroom:       OK (remember: launch via 'headroom wrap claude')" || echo "  headroom:       NOT installed"
  { have wt || have git-wt; } && echo "  worktrunk:      OK (workflow tool — outside the contract)" || echo "  worktrunk:      NOT installed (optional)"
  have opensrc && echo "  opensrc:        OK (context tool — outside the contract)" || echo "  opensrc:        NOT installed (optional)"
  grep -q '>>> claude-context-stack >>>' "$CLAUDE_MD" 2>/dev/null && echo "  contract:       OK ($CLAUDE_MD)" || echo "  contract:       MISSING"
  if [ -d .git ]; then
    [ -f graphify-out/graph.json ] && echo "  graph (here):   OK ($(du -h graphify-out/graph.json | cut -f1))" || echo "  graph (here):   not built — run: $(basename "$0") init"
    [ -x .git/hooks/post-commit ]  && echo "  post-commit:    OK" || echo "  post-commit:    none"
  fi
}

case "${1:-global}" in
  global|"")  install_global ;;
  init)       init_project ;;
  verify)     verify ;;
  contract)   [ "${2:-}" = "--condensed" ] && print_contract_condensed || print_contract ;;
  stats)      stats ;;
  -h|--help|help) sed -n '2,53p' "$0" | sed 's/^# \{0,1\}//' ;;
  *) err "unknown command: $1"; echo "usage: $(basename "$0") [global|init|verify|contract [--condensed]|stats]"; exit 1 ;;
esac

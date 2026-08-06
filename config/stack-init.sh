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
#    Global (run once): RTK hook, Serena at user scope + serena-autoinit
#      SessionStart hook (Serena does NOT activate from cwd on its own — it
#      needs a .serena/project.yml, which that hook writes per checkout),
#      graphify install + graph-autobuild SessionStart hook, Headroom
#      install + claude shim, and the routing contract in ~/.claude/CLAUDE.md.
#    Per-repo: nothing required — the first session inside any git repo builds
#      its graph in the background. `init` remains for building one eagerly (and
#      for the tracked-file extras autobuild never touches: .gitignore,
#      .claude/agents contract injection).
#
#  USAGE
#    stack-init            # or: stack-init global    -> global install (once)
#    stack-init init       # inside a repo   -> build graph + hooks eagerly
#    stack-init verify     # check everything is wired
#    stack-init contract   # print the routing contract it installs
#    stack-init contract --condensed  # print the short form injected into agents
#    stack-init stats      # append + print a usage snapshot (rtk/headroom)
#
#  AFTER GLOBAL INSTALL: open a NEW shell. Bare `claude` then launches through
#  Headroom automatically via a shim (CLAUDE_NO_HEADROOM=1 bypasses it for one
#  run), and the first session in any git repo autobuilds its graph in the
#  background (opt out: CLAUDE_STACK_NO_AUTOBUILD=1, or a .graphify-skip file
#  in the repo root).
#
#  PREREQS: git, claude (Claude Code CLI), python3 (settings.json merges), plus
#  cargo/pip/uv for the tool installs. A language server per language
#  (rust-analyzer via `rustup component add rust-analyzer`, etc.).
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
   IF absent -> orient normally (the stack autobuilds the graph in the background
   at session start - it may simply not be ready yet).
2. Specific symbols (definitions, references, implementations, file overviews)
   -> Serena (find_symbol, find_referencing_symbols, get_symbols_overview).
   Never grep for symbol names.
   Serena starts each session with NO ACTIVE PROJECT — writing .serena/project.yml
   configures it but does not activate it. If a Serena tool answers "No active
   project", call activate_project on this checkout's root (the SessionStart hook
   prints its path and name) and retry. Never take that error as a reason to grep.
3. Compile / type / lint state -> Serena get_diagnostics_for_file.
   Do not run a full type-check just to read diagnostics Serena already provides.
4. Edits to existing symbols -> Serena symbol-level edits (replace_symbol_body,
   insert_after_symbol, rename_symbol), not string/regex replacement.
5. Anything that executes (tests, builds, git, tooling) -> Bash. RTK compresses it.
   Do NOT route execution through an MCP shell tool or the PowerShell tool —
   RTK's hook matches Bash only, so both hand back uncompressed output.
   PowerShell is for genuinely Windows-only work (registry, COM, cmdlets).
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

# Skills for the extras (opensrc, worktrunk). graphify deploys its own via
# `graphify install`; these two ship none, and without a SKILL.md in
# $CLAUDE_DIR/skills Claude has the binaries on PATH but nothing ever surfaces
# them — the skill description is what makes the agent reach for the tool.
# Canonical copies live in skills/<name>/ in the agent-skills repo (SKILL.md
# plus any supporting files), where they work as ordinary standalone Claude
# skills; this script only DEPLOYS them, verbatim (no stack-specific text
# appended — the skills already carry their Context Stack interop notes).
# Source: the repo checkout next to this script — the script ships inside the
# repo, so run it from there (no network fallback by design). Non-fatal like
# the extras themselves.
script_dir() {
  # Resolve symlinks so `ln -s .../config/stack-init.sh ~/.local/bin/stack-init`
  # still finds the repo; readlink -f is GNU — fall back to the plain path.
  local p; p="$(readlink -f "$0" 2>/dev/null || echo "$0")"
  cd "$(dirname "$p")" && pwd
}

install_extra_skill() {
  local name="$1" src dst
  src="$(script_dir)/../skills/$name"
  dst="$CLAUDE_DIR/skills/$name"
  if [ ! -f "$src/SKILL.md" ]; then
    warn "$name skill not deployed — skills/$name/SKILL.md not found next to this script; run stack-init from the agent-skills repo checkout"
    return 0
  fi
  # Mirror the whole skill directory, not just SKILL.md — skills may ship
  # supporting files (references/, scripts/, ...). Delete-then-copy so files
  # removed from the repo don't linger: the deployed copy is fully managed by
  # this step, never hand-edited.
  rm -rf "$dst"
  mkdir -p "$(dirname "$dst")"
  cp -R "$src" "$dst"
  say "  $name skill deployed (from repo skills/)"
}

print_contract_condensed() {
cat <<'BLOCK'
# >>> claude-context-stack >>> (condensed, managed by stack-init — edits here are overwritten)
1. Architecture/cross-module -> graphify (graphify-out/GRAPH_REPORT.md, `graphify query`/`path`). Never grep/read-many for this.
2. Specific symbols -> Serena (find_symbol, find_referencing_symbols, get_symbols_overview). Never grep for symbol names. On "No active project", call activate_project on this checkout's root, then retry — never fall back to grep.
5. Anything that executes -> Bash (RTK compresses it). Never an MCP shell tool, and on Windows never the PowerShell tool either (RTK's hook is Bash-only) except for Windows-only work.
6. Graph = last REBUILD. Uncommitted+symbol -> Serena. Uncommitted+architectural -> `graphify update .` first, then query.
Precedence on conflict: code/LSP (Serena) > graph (graphify).
# <<< claude-context-stack <<<
BLOCK
}

# Appending straight onto a file that does not end in a newline glues the first
# line of the block onto the host document's last line - the marker stops being
# at the start of a line, so the next run's strip pass no longer matches it and
# the block is appended AGAIN. Normalise the tail to exactly one blank line
# instead of just adding one: strip-then-reappend runs in a loop over the same
# file, and an unconditional blank line grows the gap by one every run. `$( )`
# strips every trailing newline, which is what makes this converge - the same
# thing stack-init.ps1's Write-ManagedBlock does with .TrimEnd().
end_with_blank_line() {
  local f="$1" body
  [ -s "$f" ] || return 0
  body="$(cat "$f")"
  printf '%s\n\n' "$body" > "$f"
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
      local tmp
      if ! tmp="$(mktemp)"; then
        warn "$f: could not create a temporary file; skipping contract update"
        continue
      fi
      if ! awk '/>>> claude-context-stack >>>/{s=1} !s{print} /<<< claude-context-stack <<</{s=0}' \
        "$f" > "$tmp"; then
        rm -f "$tmp"
        warn "$f: could not replace the existing managed block; skipping contract update"
        continue
      fi
      if ! mv "$tmp" "$f"; then
        rm -f "$tmp"
        warn "$f: could not write the updated managed block; skipping contract update"
        continue
      fi
    fi
    end_with_blank_line "$f"
    print_contract_condensed >> "$f"
  done
  if [ "$found" = 1 ]; then say "  condensed contract injected into $dir/*.md"
  else say "  no agent files at $dir — skipping condensed contract injection"; fi
}

check_deps() {
  local miss=0
  # python3 is required, not optional: every settings.json mutation (the two
  # SessionStart hooks, MCP_TIMEOUT) and `stats` go through it. It used to be
  # undeclared, so a box without it failed deep inside install_global instead
  # of here.
  for d in git claude python3; do have "$d" || { err "missing required: $d"; miss=1; }; done
  have cargo || warn "cargo not found — needed to install RTK (Arch: pacman -S rust / rustup)"
  have pip   || warn "pip not found — needed to install graphify"
  [ "$miss" = 0 ] || { err "install the required tools above, then re-run"; exit 1; }
}

get_git_hooks_dir() {
  # Ask git for the hooks dir instead of assuming .git/hooks. In a LINKED
  # WORKTREE .git is a FILE, not a directory, so .git/hooks does not exist and
  # writing there either fails or drops hooks somewhere git never reads.
  # `rev-parse --git-path hooks` resolves core.hooksPath and worktrees alike,
  # and points every worktree at the COMMON hooks dir - which is what we want:
  # git supports one hooks dir per repo, and the bodies below are cwd-relative,
  # so they act on whichever worktree ran the command.
  git rev-parse --git-path hooks 2>/dev/null
}

in_git_repo() {
  # `.git` is a DIRECTORY only in the primary checkout - in a linked worktree it
  # is a FILE pointing at the common dir, so `[ -d .git ]` is false and every
  # worktree gets locked out of `init` and of verify's repo-local checks. Ask
  # git instead, which answers the same in both.
  git rev-parse --git-dir >/dev/null 2>&1
}

write_git_hook() {
  # Merge-not-clobber: skip if our marker is already there, append under the
  # marker if some other tool owns the file, otherwise create it fresh.
  local name="$1" body="$2" dir
  dir="$(get_git_hooks_dir)" || return 0
  [ -n "$dir" ] || return 0
  mkdir -p "$dir"
  local path="$dir/$name"
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

set_serena_dashboard_config() {
  # Dashboard stays enabled but no longer auto-opens a browser tab per
  # session; it can still be reached manually (tool call or localhost:24282).
  # No tray_manager here (unlike the ps1 installer) — Linux tray support is
  # desktop-environment dependent and untested.
  local cfg="$HOME/.serena/serena_config.yml"
  if [ ! -f "$cfg" ]; then
    say "  serena_config.yml not found (Serena writes it on first launch) — rerun global later to apply dashboard settings"
    return
  fi
  if grep -q '^web_dashboard_open_on_launch: false' "$cfg"; then
    say "  serena dashboard settings already applied"
  else
    sed -i 's/^web_dashboard_open_on_launch:.*/web_dashboard_open_on_launch: false/' "$cfg"
    say "  serena dashboard: auto-open off (still reachable manually)"
  fi
}

# Both settings.json mutations below run through one helper: same load rules,
# same refusal to clobber, one place to fix. $1 is the python body, the rest are
# argv[2:]; argv[1] is always the settings path.
edit_settings() {
  local body="$1" settings="$CLAUDE_DIR/settings.json" merge_py rc
  shift
  have python3 || { err "python3 not found - cannot edit $settings"; return 1; }
  mkdir -p "$CLAUDE_DIR"
  merge_py="$(mktemp)"
  # The preamble is shared; `body` sees `data` loaded and must call save().
  {
    cat <<'PYEOF'
import json, sys
path = sys.argv[1]
def _load():
    try:
        # utf-8-sig, not utf-8: stack-init.ps1 writes this same file, and
        # Windows PowerShell 5.1 used to stamp a UTF-8 BOM on it. A plain
        # utf-8 read raises JSONDecodeError on that byte order mark.
        with open(path, encoding='utf-8-sig') as f:
            text = f.read()
    except FileNotFoundError:
        return {}
    if not text.strip():
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # HARD STOP. The old `except: data = {}` meant one malformed byte
        # silently replaced the user's ENTIRE config on the next write -
        # RTK's PreToolUse hook, every permission, every env var. Failing to
        # install a hook is recoverable; losing that file is not.
        sys.stderr.write(
            'error: %s is not valid JSON (%s)\n'
            'refusing to overwrite it - fix or move it, then re-run\n' % (path, e))
        sys.exit(1)
data = _load()
def save():
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        f.write('\n')
PYEOF
    printf '%s\n' "$body"
  } > "$merge_py"
  # `|| rc=$?` and not a bare call: under `set -e` a failing simple command
  # exits the shell before $? can be read, so the temp file would leak and the
  # caller would never see the status.
  rc=0
  python3 "$merge_py" "$settings" "$@" || rc=$?
  rm -f "$merge_py"
  return $rc
}

register_sessionstart_hook() {
  # Adds a SessionStart command hook to global settings.json (idempotent).
  # Prints rtk-hook-present / rtk-hook-missing for callers that care.
  edit_settings '
hook_cmd = sys.argv[2]
hooks = data.setdefault("hooks", {})
starts = hooks.setdefault("SessionStart", [])
if not any(h.get("command") == hook_cmd for entry in starts for h in entry.get("hooks", [])):
    starts.append({"hooks": [{"type": "command", "command": hook_cmd}]})
save()
rtk_present = any("rtk" in str(h) for h in hooks.get("PreToolUse", []))
print("rtk-hook-present" if rtk_present else "rtk-hook-missing")
' "$1"
}

set_global_env_var() {
  # Writes settings.json env.<name> unless the user already set it (their
  # value wins - this is a floor, not a policy).
  edit_settings '
name, value = sys.argv[2], sys.argv[3]
env = data.setdefault("env", {})
if name in env:
    print("  settings.json env.%s already set (%s) - left alone" % (name, env[name]))
else:
    env[name] = value
    save()
    print("  settings.json env.%s = %s" % (name, value))
' "$1" "$2"
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

  local result
  result="$(register_sessionstart_hook "bash \"$CLAUDE_DIR/hooks/headroom-check.sh\"")"
  if [ "$result" = "rtk-hook-present" ]; then
    say "  SessionStart headroom-check hook installed; RTK PreToolUse hook still present"
  else
    warn "settings.json written but RTK's Bash hook wasn't found afterward ($result) — check $CLAUDE_DIR/settings.json manually"
  fi
}

install_graph_autobuild() {
  # Replaces per-repo `init` for the common case: a SessionStart hook that, in
  # any git repo, builds a missing graph in the background and refreshes an
  # existing one (incremental, content-hash cached). All side effects stay
  # under .git/ (hooks, info/exclude, lock) — it never mutates tracked files,
  # which is why it writes .git/info/exclude rather than .gitignore and does
  # NOT inject the condensed contract into repo .claude/agents/. Run `init`
  # for the eager/tracked-file variant.
  mkdir -p "$CLAUDE_DIR/hooks"
  cat > "$CLAUDE_DIR/hooks/graph-autobuild.sh" <<'HOOK'
#!/bin/sh
# claude-context-stack: per-repo graph autobuild/refresh at session start.
# Opt out: CLAUDE_STACK_NO_AUTOBUILD=1, or a .graphify-skip file in the repo
# root. Remove the SessionStart entry in settings.json to uninstall.
top=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
[ -n "$top" ] || exit 0
cd "$top" || exit 0
gd=$(git rev-parse --git-dir 2>/dev/null) || exit 0
cgd=$(git rev-parse --git-common-dir 2>/dev/null)
[ -n "$cgd" ] || cgd=$gd
lock="$gd/claude-stack-autobuild.lock"

# Points graphify's post-commit hook at an interpreter that can actually import
# graphify, by writing the override file the hook reads when its baked-in pin is
# dead. NO_COLOR plus the SGR strip are load-bearing: uv colourises even when
# redirected, and the hook allowlists this file's contents against
# [a-zA-Z0-9/_.@:-], so one stray escape byte makes it discard the override.
repair_graphify_python() {
  _pin="$top/graphify-out/.graphify_python"
  if [ -f "$_pin" ]; then
    _cur=$(tr -d ' \t\r\n' < "$_pin" 2>/dev/null)
    if [ -n "$_cur" ] && [ -x "$_cur" ]; then return 0; fi
  fi
  _esc=$(printf '\033')
  _ud=$(NO_COLOR=1 uv tool dir 2>/dev/null | tr -d '\r' | head -1 | sed "s/${_esc}\[[0-9;]*m//g")
  [ -n "$_ud" ] || return 0
  for _rel in graphifyy/bin/python graphifyy/Scripts/python.exe; do
    _cand="$_ud/$_rel"
    [ -x "$_cand" ] || continue
    "$_cand" -c 'import graphify' >/dev/null 2>&1 || continue
    mkdir -p "$(dirname "$_pin")"
    printf '%s' "$_cand" > "$_pin"
    return 0
  done
  return 0
}

# Repo-local git hooks that keep the graph fresh. Idempotent, and deliberately
# NOT confined to the first build: a repo whose graph predates this logic hits
# the fast path below and returns early, so it would never acquire the refresh
# hooks and would keep a stale post-commit pin forever.
ensure_repo_hooks() {
  hooks_dir="$cgd/hooks"
  mkdir -p "$hooks_dir"
  # post-commit is graphify's own hook. Install it when absent. When it exists
  # but the interpreter it pinned at install time has gone away (interpreter
  # uninstalled, pip -> uv tool migration), a plain re-install is NOT a repair:
  # graphify matches its own marker, reports "already installed" and leaves the
  # dead pin, so every commit silently fails to rebuild the graph. `hook
  # uninstall` + `hook install` does re-pin, but uninstall deletes .gitattributes
  # when the merge driver is its only entry - too destructive to run unattended
  # at session start. Repair via graphify's documented second detection path
  # instead. Only POSIX pins are probed here; a Windows pin is the .ps1
  # variant's business.
  _pc="$hooks_dir/post-commit"
  if [ ! -f "$_pc" ] || ! grep -q 'graphify-hook-start' "$_pc" 2>/dev/null; then
    graphify hook install >/dev/null 2>&1
  else
    _pin=$(sed -n "s/^_PINNED='\(.*\)'\$/\1/p" "$_pc" 2>/dev/null | head -1)
    case "$_pin" in
      /*) [ -x "$_pin" ] || repair_graphify_python ;;
    esac
  fi
  write_hook() {
    p="$hooks_dir/$1"
    if [ -f "$p" ] && grep -q 'claude-context-stack:' "$p" 2>/dev/null; then return 0; fi
    if [ -f "$p" ]; then printf '\n%s\n' "$2" >> "$p"; else printf '#!/bin/sh\n%s\n' "$2" > "$p"; fi
    chmod +x "$p"
  }
  write_hook post-checkout '# claude-context-stack: refresh graph on branch switch (not file checkout)
if [ "$3" = "1" ] && command -v graphify >/dev/null 2>&1 && [ -d graphify-out ]; then
  ( graphify update . >/dev/null 2>&1 & )
fi'
  write_hook post-merge '# claude-context-stack: refresh graph after merge/pull
command -v graphify >/dev/null 2>&1 && [ -d graphify-out ] && graphify update . >/dev/null 2>&1 || true'
  write_hook post-rewrite '# claude-context-stack: refresh graph after rebase
command -v graphify >/dev/null 2>&1 && [ -d graphify-out ] && graphify update . >/dev/null 2>&1 || true'
  return 0
}

if [ "${1:-}" = "--build" ]; then
  # Background worker: the actual first build. Everything it writes lives
  # under .git/ - never a tracked file (no .gitignore, no .claude/agents).
  trap 'rm -rf "$lock"' EXIT
  graphify . >/dev/null 2>&1
  ensure_repo_hooks
  mkdir -p "$cgd/info"
  grep -q '^graphify-out/' "$cgd/info/exclude" 2>/dev/null || printf '\ngraphify-out/\n' >> "$cgd/info/exclude"
  exit 0
fi

[ -n "${CLAUDE_STACK_NO_AUTOBUILD:-}" ] && exit 0
[ -f .graphify-skip ] && exit 0
command -v graphify >/dev/null 2>&1 || exit 0

if [ -d graphify-out ]; then
  # Backfill for repos whose graph predates this hook logic, and self-heal for a
  # dead post-commit pin. Both checks are file tests that no-op once satisfied.
  ensure_repo_hooks
  ( graphify update . >/dev/null 2>&1 & )
  exit 0
fi

if ! mkdir "$lock" 2>/dev/null; then
  # a build is (or was) running; treat locks older than 60 min as stale
  [ -n "$(find "$lock" -maxdepth 0 -mmin +60 2>/dev/null)" ] || exit 0
  rm -rf "$lock"
  mkdir "$lock" 2>/dev/null || exit 0
fi
( nohup sh "$0" --build >/dev/null 2>&1 & )
printf '%s' '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"graphify: no graph in this repo yet - the stack is building one in the background (first build can take a while on big repos). Orient normally until graphify-out/ appears; do not run graphify . yourself."}}'
exit 0
HOOK
  chmod +x "$CLAUDE_DIR/hooks/graph-autobuild.sh"
  register_sessionstart_hook "bash \"$CLAUDE_DIR/hooks/graph-autobuild.sh\"" >/dev/null
  say "  SessionStart graph-autobuild hook installed (opt out: CLAUDE_STACK_NO_AUTOBUILD=1 or .graphify-skip)"
}

install_serena_autoinit() {
  # Serena does NOT auto-activate from cwd — the claim this installer shipped
  # with was wrong. With no .serena/project.yml it starts with NO active
  # project and every symbol tool fails with "No active project", which is
  # silent: the model just falls back to grep, breaking contract rule 2 with
  # nothing in the UI to say so (the same failure mode as a timed-out MCP
  # launch). Serena's own detection is also too weak to rely on — on a repo of
  # 21 markdown + 1 shell + 1 powershell file it selected powershell alone, so
  # every other file answered "path is ignored". Languages are derived from
  # tracked files here instead.
  mkdir -p "$CLAUDE_DIR/hooks"
  cat > "$CLAUDE_DIR/hooks/serena-autoinit.sh" <<'HOOK'
#!/bin/sh
# claude-context-stack: per-checkout Serena project init at session start.
# Opt out: CLAUDE_STACK_NO_SERENA_INIT=1, or a .serena-skip file in the root.
# Uninstall: remove the SessionStart entry in settings.json.
[ -n "${CLAUDE_STACK_NO_SERENA_INIT:-}" ] && exit 0
command -v serena >/dev/null 2>&1 || exit 0
top=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
[ -n "$top" ] || exit 0
cd "$top" || exit 0
[ -f .serena-skip ] && exit 0

gd=$(git rev-parse --git-dir 2>/dev/null) || exit 0
cgd=$(git rev-parse --git-common-dir 2>/dev/null)
[ -n "$cgd" ] || cgd=$gd

proj=".serena/project.yml"
marker="Generated by claude-context-stack (serena-autoinit)"

# Keep the generated folder out of git without touching a tracked .gitignore —
# same rule the graph autobuild hook follows. Written to the COMMON git dir so
# one entry covers the main checkout and every worktree hanging off it.
ensure_serena_excluded() {
  mkdir -p "$cgd/info"
  grep -q '^\.serena/$' "$cgd/info/exclude" 2>/dev/null || printf '\n.serena/\n' >> "$cgd/info/exclude"
}

# Writing project.yml does NOT make Serena use it: the MCP server starts with NO
# active project, and every symbol tool then fails with "No active project" until
# something calls activate_project. That failure is silent — the model just falls
# back to grep, breaking contract rule 2 with nothing in the UI to say so. So the
# hook ALWAYS ends by naming the project to activate, whether it wrote one,
# repaired one, or found a good one already there.
emit_activation() {
  ensure_serena_excluded
  _msg="Serena project for this checkout: '$1' at $top. Serena starts with NO active project - call activate_project with that path before the first symbol query, and whenever a tool answers 'No active project'."
  [ -n "${2:-}" ] && _msg="$_msg $2"
  printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}' "$_msg"
  exit 0
}

# Falls back to the name derived below, so a config with no project_name key
# still yields the branch-suffixed name a linked worktree needs.
project_name_of() {
  _n=$(sed -n 's/^[[:space:]]*project_name[[:space:]]*:[[:space:]]*"\{0,1\}\([^"]*\)"\{0,1\}[[:space:]]*$/\1/p' "$1" 2>/dev/null | head -1)
  [ -n "$_n" ] || _n="$name"
  printf '%s' "$_n"
}

# Entries of the YAML `language_servers:` block. Only `- name` lines are
# collected, so scanning past blank/comment lines to the next real key cannot
# invent entries; the first non-list, non-blank, non-comment line ends the block.
configured_servers() {
  awk '
    /^[[:space:]]*language_servers[[:space:]]*:/ { inlist=1; next }
    !inlist { next }
    /^[[:space:]]*-[[:space:]]*"?[A-Za-z0-9_]+"?[[:space:]]*$/ {
      gsub(/^[[:space:]]*-[[:space:]]*"?/, ""); gsub(/"?[[:space:]]*$/, "")
      print tolower($0); next
    }
    /^[[:space:]]*(#.*)?$/ { next }
    { exit }
  ' "$1" 2>/dev/null
}

write_project_yml() {
  mkdir -p "$(dirname "$1")"
  {
    echo "# Generated by claude-context-stack (serena-autoinit). Safe to edit or"
    echo "# delete: while this header is present the file is left alone. A config"
    echo "# WITHOUT this header came from Serena auto-detection and is repaired"
    echo "# (original kept as project.yml.bak-*) when its language_servers list"
    echo "# misses a language present in this checkout. Machine-local overrides"
    echo "# belong in project.local.yml, which Serena ignores by default."
    printf 'project_name: "%s"\n' "$2"
    echo 'language_servers:'
    for s in $servers; do echo "- $s"; done
    echo 'ignore_all_files_in_gitignore: true'
    if [ "$gd" = "$cgd" ]; then
      # Worktrunk nests linked worktrees at .claude/worktrees/ INSIDE the main
      # checkout, so without this the main project indexes every worktree as well
      # and one symbol lookup returns a near-duplicate hit per branch. Emitted
      # unconditionally: worktrees usually appear after this file is generated,
      # and it is inert when the directory does not exist.
      echo 'ignored_paths:'
      echo '- ".claude/worktrees"'
    fi
  } > "$1"
}

# Worktrunk: a linked worktree is a separate checkout at its own path, and
# project_serena_folder_location is "$projectDir/.serena", so each worktree
# needs its own project rather than inheriting the main one. serena_config.yml
# keys the registry by path, but names are what activation and the dashboard
# show, so linked worktrees are suffixed with their branch to stay distinct.
name=$(basename "$top")
if [ "$gd" != "$cgd" ]; then
  br=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
  [ -n "$br" ] && [ "$br" != "HEAD" ] && name="$name@$br"
fi

exts=$(git ls-files 2>/dev/null | sed -n 's/.*\.\([A-Za-z0-9_]*\)$/\1/p' | tr 'A-Z' 'a-z' | sort -u)
if [ -z "$exts" ]; then
  [ -f "$proj" ] && emit_activation "$(project_name_of "$proj")"
  exit 0
fi
has() { printf '%s\n' "$exts" | grep -qx "$1"; }
servers=""
add() { case " $servers " in *" $1 "*) ;; *) servers="$servers $1" ;; esac; }
# Compiled/checked languages first: the FIRST entry is Serena's default and
# fallback server, so a real language should outrank markdown/yaml here.
has rs && add rust
has py && add python
for e in ts tsx js jsx mjs cjs; do has "$e" && add typescript; done
has go && add go
has java && add java
has kt && add kotlin
has cs && add csharp
for e in c h cpp hpp cc hh; do has "$e" && add cpp; done
has rb && add ruby
has php && add php
has swift && add swift
has scala && add scala
has lua && add lua
has zig && add zig
for e in ex exs; do has "$e" && add elixir; done
has tf && add terraform
for e in sh bash; do has "$e" && add bash; done
for e in ps1 psm1 psd1; do has "$e" && add powershell; done
has md && add markdown
for e in yml yaml; do has "$e" && add yaml; done
has toml && add toml
if [ -z "$servers" ]; then
  [ -f "$proj" ] && emit_activation "$(project_name_of "$proj")"
  exit 0
fi

if [ -f "$proj" ]; then
  # Ours already: left alone for good, so hand edits to it survive every session.
  grep -qF "$marker" "$proj" 2>/dev/null && emit_activation "$(project_name_of "$proj")"
  # Not ours, so Serena's own auto-detection wrote it — and that detection is too
  # weak to leave in place: on the agent-skills repo (mostly markdown, one .sh,
  # one .ps1) it selected `powershell` ALONE, so get_symbols_overview on any .md
  # or .sh answered "Cannot extract symbols ... Active language servers:
  # ['powershell']" and the model silently fell back to grep. Repair only when the
  # file actually misses a language present here, and never destroy the original.
  configured=$(configured_servers "$proj")
  missing=""
  for s in $servers; do
    printf '%s\n' "$configured" | grep -qx "$s" || missing="$missing $s"
  done
  [ -n "$missing" ] || emit_activation "$(project_name_of "$proj")"
  had=$(printf '%s' "$configured" | tr '\n' ' ')
  bak="$proj.bak-$(date +%Y%m%d%H%M%S)"
  cp -p "$proj" "$bak"
  # Repair fixes only what was broken: the name it was registered under is kept,
  # so an intentionally renamed project does not silently change identity.
  rname=$(project_name_of "$proj")
  write_project_yml "$proj" "$rname"
  emit_activation "$rname" "Its language_servers were repaired (had: $had; missing:$missing); the previous file is kept at $bak."
fi

write_project_yml "$proj" "$name"
emit_activation "$name"
HOOK
  chmod +x "$CLAUDE_DIR/hooks/serena-autoinit.sh"
  register_sessionstart_hook "bash \"$CLAUDE_DIR/hooks/serena-autoinit.sh\"" >/dev/null
  say "  SessionStart serena-autoinit hook installed (opt out: CLAUDE_STACK_NO_SERENA_INIT=1 or .serena-skip)"
}

install_claude_shim() {
  # Shadows bare `claude` so it launches through Headroom automatically. The
  # self-recursion hazard that made shadowing dangerous (headroom re-resolving
  # 'claude' back to the shim - `headroom wrap` only accepts tool names, so
  # re-resolution is unavoidable) is bounded by construction: the shim exports
  # a re-entry guard (CLAUDE_STACK_SHIM) before delegating, so when headroom's
  # PATH search lands back on the shim, that second entry execs the REAL
  # binary (which the shim resolves itself, skipping its own directory) -
  # exactly one bounce, never a loop. An already-wrapped session (localhost
  # ANTHROPIC_BASE_URL) is never double-wrapped. Headroom missing or
  # CLAUDE_NO_HEADROOM=1 falls through to the real binary - a broken shim
  # never blocks a session.
  # $1 carries ' --no-tokensave' when supported: newer headroom builds its own
  # code graph by default, which the decisions log forbids (duplicate of
  # graphify; see the --code-graph entry).
  local headroom_flags="${1:-}" bin_dir="$CLAUDE_DIR/stack-bin" rc line
  mkdir -p "$bin_dir"
  cat > "$bin_dir/claude" <<'SHIM'
#!/bin/sh
# claude-context-stack: auto-wrap claude with Headroom (managed by stack-init).
# CLAUDE_NO_HEADROOM=1 skips wrapping for one launch; delete this file (and
# its PATH entry) to remove the shim entirely.
self_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
real=
old_ifs=$IFS
IFS=:
for d in $PATH; do
  [ -n "$d" ] || continue
  [ "$(CDPATH= cd -- "$d" 2>/dev/null && pwd -P)" = "$self_dir" ] && continue
  for n in claude claude.exe claude.cmd; do
    if [ -f "$d/$n" ] && [ -x "$d/$n" ]; then real="$d/$n"; break 2; fi
  done
done
IFS=$old_ifs
if [ -z "$real" ]; then
  echo "claude shim: real claude binary not found on PATH" >&2
  exit 127
fi
wrapped=
case "${ANTHROPIC_BASE_URL:-}" in *127.0.0.1*|*localhost*) wrapped=1 ;; esac
if [ -n "${CLAUDE_NO_HEADROOM:-}" ] || [ -n "${CLAUDE_STACK_SHIM:-}" ] || [ -n "$wrapped" ] \
   || ! command -v headroom >/dev/null 2>&1; then
  exec "$real" "$@"
fi
CLAUDE_STACK_SHIM=1
export CLAUDE_STACK_SHIM
SHIM
  printf 'exec headroom wrap claude%s "$@"\n' "$headroom_flags" >> "$bin_dir/claude"
  chmod +x "$bin_dir/claude"
  say "  shim written -> $bin_dir/claude"
  line="export PATH=\"$bin_dir:\$PATH\"  # claude-context-stack shim"
  for rc in "$HOME/.profile" "$HOME/.bashrc" "$HOME/.zshrc"; do
    grep -q 'claude-context-stack shim' "$rc" 2>/dev/null && continue
    printf '\n%s\n' "$line" >> "$rc"
  done
  say "  PATH prepend added to .profile/.bashrc/.zshrc (open a NEW shell to pick it up)"
  case ":$PATH:" in *":$bin_dir:"*) ;; *) PATH="$bin_dir:$PATH" ;; esac
}

install_global() {
  check_deps
  say "RTK — output compression (global Bash hook)"
  if have rtk; then say "  rtk present ($(rtk --version 2>/dev/null))"
  else say "  installing rtk"; cargo install --git https://github.com/rtk-ai/rtk; fi
  rtk init -g && say "  rtk init -g (PreToolUse Bash hook registered)"

  # One health-check pass, reused by the Serena and Headroom steps below:
  # `claude mcp list` spawns every registered server and waits on it, so
  # calling it twice doubles the slowest step in this function.
  local mcp_list serena_line
  mcp_list="$(claude mcp list 2>/dev/null)"

  say "Serena — LSP symbols over MCP (user scope, one project per checkout)"
  install_uv
  # Serena runs from a uv-installed binary, NOT `uvx --from git+...`: uvx
  # re-resolves the git ref and REBUILDS the package whenever uv's cache is
  # cold, which overruns Claude Code's 30s MCP startup limit and leaves the
  # session with no Serena at all. That failure is silent — the model just
  # falls back to grep, breaking contract rule 2 with nothing in the UI to
  # say so. `uv tool install` pins a built binary, so launch is import-only.
  if have serena; then say "  serena present ($(serena --version 2>/dev/null))"
  else
    say "  installing serena (uv tool; PyPI/dist name is serena-agent, command is serena)"
    uv tool install --from git+https://github.com/oraios/serena serena-agent
  fi
  # Migrate an earlier uvx-based registration — a bare "already registered"
  # check would leave the slow, timeout-prone form in place forever.
  serena_line="$(printf '%s\n' "$mcp_list" | grep -i '^serena[: ]' || true)"
  case "$serena_line" in
    *uvx*)
      claude mcp remove --scope user serena >/dev/null 2>&1
      say "  removed uvx-based serena registration (rebuilt from git on every launch)"
      serena_line=""
      ;;
  esac
  if [ -n "$serena_line" ]; then
    say "  serena already registered — skipped"
  else
    # --context claude-code is the current name of the old 'ide-assistant'
    # context (Serena logs a deprecation warning for the latter); same
    # toolset, shell/read/file-search tools excluded so it can't shadow
    # Bash+RTK or the built-in file tools.
    claude mcp add --scope user serena -- serena start-mcp-server --context claude-code
    say "  serena registered at user scope (--context claude-code: no shell/read tools)"
  fi
  # Safety net for a genuinely cold first launch (uv tool run, LSP download):
  # Claude Code's default MCP startup timeout is 30s, which is not much.
  set_global_env_var MCP_TIMEOUT 120000
  set_serena_dashboard_config

  say "serena autoinit — per-checkout project, automated (SessionStart hook)"
  install_serena_autoinit

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

  say "graph autobuild — per-repo init, automated (SessionStart hook)"
  install_graph_autobuild

  say "Headroom — proxy-layer compression (final pass before the API)"
  if have headroom; then say "  headroom present ($(headroom --version 2>/dev/null))"
  else
    say "  installing headroom (PyPI package: headroom-ai)"
    if have uv; then uv tool install 'headroom-ai[all]'; else pip install 'headroom-ai[all]'; fi
  fi
  # Headroom integrates at the WIRE (the shim below), never as an MCP server.
  # A `headroom mcp serve` registration is not part of this stack and current
  # headroom-ai builds crash on its startup (AttributeError: 'Server' object
  # has no attribute 'list_tools'), so each session pays ~3s for a connection
  # that always fails, in every workspace. Drop a stray one.
  if printf '%s\n' "$mcp_list" | grep -qi '^headroom[: ]'; then
    claude mcp remove --scope user headroom >/dev/null 2>&1
    say "  removed stray headroom MCP registration (wire proxy is the integration, not MCP)"
  fi
  # Newer headroom builds its own "tokensave" code graph by default - the
  # renamed, default-on incarnation of --code-graph, which the decisions log
  # forbids as a duplicate of graphify. Disable it when the flag exists;
  # probing keeps older headroom versions (no such flag) launching cleanly.
  HEADROOM_FLAGS=""
  headroom wrap claude --help 2>/dev/null | grep -q -- '--no-tokensave' && HEADROOM_FLAGS=" --no-tokensave"
  say "  shadowing bare 'claude' with a recursion-safe shim (see install_claude_shim"
  say "  for how the old self-recursion hazard is closed)"
  install_claude_shim "$HEADROOM_FLAGS"
  # The shim supersedes the 2.2 clw/hclaude/claudew wrapper - remove any of
  # ours a previous version wrote. Manual fallback is `headroom wrap claude`.
  for old in clw hclaude claudew; do
    if [ -f "$HOME/.local/bin/$old" ] && grep -q 'headroom wrap claude' "$HOME/.local/bin/$old" 2>/dev/null; then
      rm -f "$HOME/.local/bin/$old"
      say "  removed obsolete wrapper: $old (the shim replaces it)"
    fi
  done
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
  # non-fatal: a worktrunk failure must never block the token stack. Bare `wt`
  # is fine here (unlike stack-init.ps1's Windows detection): brew and cargo
  # both install the binary as plain `wt` on this platform, and there's no
  # Windows-Terminal-style collision to dodge — `git-wt` is only a defensive
  # fallback, not the primary name.
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
      warn "claude-context-stack = \"[ -d '{{ primary_worktree_path }}/graphify-out' ] && graphify . && graphify hook install && cp -n '{{ primary_worktree_path }}/graphify-out/.graphify_python' graphify-out/ 2>/dev/null || true\""
    else
      cat >> "$WT_CFG" <<'WTHOOK'

# claude-context-stack: replicate the stack's per-checkout state (graphify graph,
# post-commit rebuild hook, interpreter pin) into every new worktree, only where
# the primary checkout was stack-inited. The .graphify_python copy matters
# because the post-commit hook is SHARED across worktrees but reads its override
# relative to cwd - without it a new worktree's first commit warns instead of
# rebuilding, until a Claude session's autobuild hook repairs it.
# Delete this block to opt out.
[post-start]
claude-context-stack = "[ -d '{{ primary_worktree_path }}/graphify-out' ] && graphify . && graphify hook install && cp -n '{{ primary_worktree_path }}/graphify-out/.graphify_python' graphify-out/ 2>/dev/null || true"
WTHOOK
      say "  global post-start hook written -> $WT_CFG"
    fi
  else
    warn "worktrunk unavailable — parallel-worktree support skipped (stack unaffected)"
  fi

  say "Extras' skills -> $CLAUDE_DIR/skills (opensrc, worktrunk)"
  # Deployed unconditionally (even if a binary install above failed — both are
  # global tools the user may add later, and the worktrunk skill itself covers
  # offering the install) and idempotently: overwritten every run, like the
  # contract. See install_extra_skill for source resolution.
  install_extra_skill opensrc
  install_extra_skill worktrunk

  say "Routing contract -> $CLAUDE_MD"
  mkdir -p "$CLAUDE_DIR"; touch "$CLAUDE_MD"
  if grep -q '>>> claude-context-stack >>>' "$CLAUDE_MD"; then
    local tmp; tmp="$(mktemp)"
    awk '/>>> claude-context-stack >>>/{s=1} !s{print} /<<< claude-context-stack <<</{s=0}' \
      "$CLAUDE_MD" > "$tmp" && mv "$tmp" "$CLAUDE_MD"
    say "  refreshed existing managed block"
  fi
  end_with_blank_line "$CLAUDE_MD"
  print_contract >> "$CLAUDE_MD"
  say "  contract written (idempotent — re-running replaces the managed block)"

  say "Condensed contract -> subagent files (~/.claude/agents/)"
  inject_condensed_contract "$CLAUDE_DIR/agents"

  have rust-analyzer || warn "rust-analyzer not on PATH — Serena needs it for Rust (rustup component add rust-analyzer)"
  echo; say "Global install done. Open a NEW shell so the claude shim takes effect."
  say "No per-repo step needed — the first session in any git repo autobuilds its"
  say "graph ('$(basename "$0") init' still works for an eager build)."
}

init_project() {
  in_git_repo || { err "run from a git repo (no git repo here)"; exit 1; }
  have graphify || { err "graphify not installed — run '$(basename "$0") global' first"; exit 1; }
  # Everything below is repo-ROOT state: `graphify .` from a subdirectory would
  # build a graph of that subdirectory alone and drop .gitignore there, while
  # the autobuild hook (which cd's to the top level) builds the real one — two
  # graphs, one repo. Match the hook and move to the top first.
  local top
  top="$(git rev-parse --show-toplevel 2>/dev/null)" || top=""
  [ -n "$top" ] && { cd "$top" && say "repo root: $top"; }
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
  # `headroom savings`, not `headroom stats` - the latter has never been a
  # headroom subcommand, so every snapshot ever taken recorded a usage error
  # instead of the numbers. (`headroom memory stats` exists and is a different
  # thing: memory-store counts, not compression savings.)
  if have rtk; then rtk_out="$(rtk gain 2>&1 || true)"; else rtk_out="rtk not on PATH"; fi
  if have headroom; then headroom_out="$(headroom savings 2>&1 || true)"; else headroom_out="headroom not installed"; fi
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
  # Read the registered hook, do NOT shell out to `rtk gain`: it exits 0 whether
  # or not a hook exists (it merely prints a warning), so the old check reported
  # "active" for an uninstalled hook. settings.json is the source of truth.
  if grep -q '"PreToolUse"' "$CLAUDE_DIR/settings.json" 2>/dev/null &&
     grep -q 'rtk' "$CLAUDE_DIR/settings.json" 2>/dev/null; then
    echo "  rtk hook:       OK (PreToolUse Bash)"
  else echo "  rtk hook:       NOT registered — run: rtk init -g"; fi
  claude mcp list 2>/dev/null | grep -qi serena && echo "  serena (mcp):   OK (user scope)" || echo "  serena (mcp):   NOT registered"
  have graphify && echo "  graphify:       OK" || echo "  graphify:       NOT installed"
  have headroom && echo "  headroom:       OK" || echo "  headroom:       NOT installed"
  if [ -x "$CLAUDE_DIR/stack-bin/claude" ]; then
    first="$(command -v claude 2>/dev/null || true)"
    if [ "$first" = "$CLAUDE_DIR/stack-bin/claude" ]; then echo "  claude shim:    OK (bare 'claude' auto-wraps through headroom)"
    else echo "  claude shim:    installed but NOT first on PATH (open a new shell?)"; fi
  else echo "  claude shim:    NOT installed"; fi
  if [ -x "$CLAUDE_DIR/hooks/graph-autobuild.sh" ] && grep -q 'graph-autobuild' "$CLAUDE_DIR/settings.json" 2>/dev/null; then
    echo "  graph autobuild: OK (SessionStart)"
  else echo "  graph autobuild: NOT registered"; fi
  if [ -x "$CLAUDE_DIR/hooks/serena-autoinit.sh" ] && grep -q 'serena-autoinit' "$CLAUDE_DIR/settings.json" 2>/dev/null; then
    echo "  serena autoinit: OK (SessionStart)"
  else echo "  serena autoinit: NOT registered"; fi
  { have wt || have git-wt; } && echo "  worktrunk:      OK (workflow tool — outside the contract)" || echo "  worktrunk:      NOT installed (optional)"
  have opensrc && echo "  opensrc:        OK (context tool — outside the contract)" || echo "  opensrc:        NOT installed (optional)"
  [ -f "$CLAUDE_DIR/skills/opensrc/SKILL.md" ]   && echo "  opensrc skill:    OK (global)"   || echo "  opensrc skill:    NOT deployed — rerun global"
  [ -f "$CLAUDE_DIR/skills/worktrunk/SKILL.md" ] && echo "  worktrunk skill:  OK (global)"   || echo "  worktrunk skill:  NOT deployed — rerun global"
  grep -q '>>> claude-context-stack >>>' "$CLAUDE_MD" 2>/dev/null && echo "  contract:       OK ($CLAUDE_MD)" || echo "  contract:       MISSING"
  if in_git_repo; then
    # Everything below is PER CHECKOUT, and a linked worktree is a checkout like
    # any other: it gets its own graph and its own Serena project, because both
    # describe the code at THIS path. Only the hooks are shared — git supports
    # one hooks dir per repo — which is fine, since the bodies are cwd-relative
    # and so act on whichever worktree invoked them.
    local gd cgd hooks_dir br refresh_hook refresh_hooks_ok=1
    # Both paths can come back relative, and there is no portable absolute form
    # (--path-format needs git 2.31+), so normalise BOTH through `cd && pwd -P`.
    # Doing it to only one side would leave the comparison symlink-sensitive and
    # a worktree would look linked (or not) depending on how the repo was reached.
    gd="$(git rev-parse --git-dir 2>/dev/null)"
    [ -n "$gd" ] && gd="$(CDPATH= cd -- "$gd" 2>/dev/null && pwd -P)"
    cgd="$(git rev-parse --git-common-dir 2>/dev/null)"
    [ -n "$cgd" ] && cgd="$(CDPATH= cd -- "$cgd" 2>/dev/null && pwd -P)"
    [ -n "$cgd" ] || cgd="$gd"
    if [ -n "$gd" ] && [ "$gd" != "$cgd" ]; then
      br="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
      echo "  checkout:       linked worktree ($br) — own graph + Serena project, shared hooks"
    else echo "  checkout:       primary"; fi
    # Anchor on the repo ROOT, never cwd: graphify-out/ and .serena/ are written
    # at the top level by the SessionStart hooks (which `cd "$top"` first), so
    # cwd-relative tests reported "not built" / "none" for a fully wired repo
    # whenever verify ran from a subdirectory.
    local top
    top="$(git rev-parse --show-toplevel 2>/dev/null)" || top=""
    [ -n "$top" ] || top="$PWD"
    [ -f "$top/graphify-out/graph.json" ] && echo "  graph (here):   OK ($(du -h "$top/graphify-out/graph.json" | cut -f1))" || echo "  graph (here):   not built — autobuilds next session (or run: $(basename "$0") init)"
    [ -f "$top/.serena/project.yml" ] && echo "  serena project: OK (.serena/project.yml)" || echo "  serena project: none — autoinits next session"
    hooks_dir="$(get_git_hooks_dir)"
    [ -n "$hooks_dir" ] || hooks_dir=".git/hooks"
    [ -f "$hooks_dir/post-commit" ] && echo "  post-commit:    OK" || echo "  post-commit:    none"
    for refresh_hook in post-checkout post-merge post-rewrite; do
      grep -q 'claude-context-stack:' "$hooks_dir/$refresh_hook" 2>/dev/null || { refresh_hooks_ok=0; break; }
    done
    [ "$refresh_hooks_ok" = 1 ] && echo "  graph refresh:  OK (checkout/merge/rewrite)" || echo "  graph refresh:  MISSING (checkout/merge/rewrite)"
  fi
}

case "${1:-global}" in
  global|"")  install_global ;;
  init)       init_project ;;
  verify)     verify ;;
  contract)   [ "${2:-}" = "--condensed" ] && print_contract_condensed || print_contract ;;
  stats)      stats ;;
  # Print the whole comment banner, however long it grows. The old fixed
  # '2,57p' range silently truncated it mid-sentence once the header moved -
  # by the time this was noticed it was cutting the PREREQS line off.
  -h|--help|help) awk 'NR==1{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "$0" ;;
  *) err "unknown command: $1"; echo "usage: $(basename "$0") [global|init|verify|contract [--condensed]|stats]"; exit 1 ;;
esac

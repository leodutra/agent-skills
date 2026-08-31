#!/usr/bin/env bash
# =============================================================================
#  Claude Code Context Stack  —  global installer  (Linux/macOS)
# =============================================================================
#
#  WHAT THIS IS
#  A routing contract plus two components, built on one rule learned the hard
#  way: eliminate waste at its source, never compress downstream.
#
#    Serena    symbols    LSP over MCP (rust-analyzer / tsserver / pyright).
#                         Kills RETRIEVAL+EDIT cost — exact symbol defs, refs,
#                         diagnostics and symbol-level edits instead of
#                         whole-file dumps and grep walls.
#                         OPT-IN: registered but DISABLED. Its tool manifest is
#                         a fixed per-session tax and it loses on cheap lookups,
#                         so you turn it on with /mcp for refactor, test-writing
#                         and architecture work on bigger repos (D53).
#    ponytail  discipline Claude Code plugin (skill + SessionStart hook) that
#                         injects a minimal-code ruleset. Default-on. Kills code
#                         that never needed writing. Intercepts nothing — its
#                         whole mechanism is text reaching the model (D54).
#
#  REMOVED IN 3.0: graphify, RTK and Headroom. Headroom went on measurement —
#  only 25% of the tokens it reported saving ever reached the wire, and four
#  prefix-cache busts cost more than everything it saved (D49, D50, D51). RTK
#  went because its numbers were never checked and it was inert in practice
#  (D51). graphify went with all per-repo state (D52). Orientation and
#  tool-output noise are now explicitly UNOWNED — that is the honest state, not
#  a gap to paper over.
#
#  DESIGN PRINCIPLE: prefer instructing over intercepting. Every layer removed
#  in 3.0 sat in a path (before the shell, before the API, on disk) and each
#  broke in a way that was a property of being there.
#
#  WHAT IS GLOBAL vs PER-REPO
#    Global (run once): Serena at user scope (registered, disabled) +
#      serena-autoinit SessionStart hook (Serena does NOT activate from cwd on
#      its own — it needs a .serena/project.yml, which that hook writes per
#      checkout), the ponytail plugin, and the routing contract in
#      ~/.claude/CLAUDE.md.
#    Per-repo: nothing. 3.0 holds no per-repo state and installs no git hooks.
#
#  USAGE
#    stack-init            # or: stack-init global    -> global install (once)
#    stack-init skills     # list this repo's deployable skills and where each is
#    stack-init skills <name>...  # inside a repo -> symlink domain skills into
#                          # .claude/skills/ (--copy for a committable copy);
#                          # domain skills stay OUT of the global install (D48)
#    stack-init verify     # check everything is wired
#    stack-init verify --docs  # check THIS REPO's docs: every section and
#                          # decision reference resolves (maintenance, not install)
#    stack-init contract   # print the routing contract it installs
#    stack-init contract --condensed  # print the short form injected into agents
#    stack-init help       # or -h / --help -> print this banner
#
#  The contract text itself is NOT in this script: it lives in contract.md and
#  contract-condensed.md next to it, which stack-init.ps1 reads too, so the two
#  installers cannot drift on the one artifact they both write.
#
#  PREREQS: git, claude (Claude Code CLI), python3 (settings.json merges), node
#  (ponytail's hooks; must be on the NON-INTERACTIVE shell's PATH), uv (Serena).
#  A language server per language (rust-analyzer via
#  `rustup component add rust-analyzer`, etc.).
# =============================================================================
set -euo pipefail

CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
CLAUDE_MD="$CLAUDE_DIR/CLAUDE.md"
# The generated SessionStart hook is also the ONE implementation of "give this
# checkout its git hooks": `init` runs it with --hooks rather than carrying a
# second copy of the same three hook bodies (which is what it used to do, minus
# the post-commit pin repair the copy never learned about).
GRAPH_AUTOBUILD_HOOK="$CLAUDE_DIR/hooks/graph-autobuild.sh"
B='\033[1;32m'; Y='\033[1;33m'; R='\033[1;31m'; N='\033[0m'
say()  { printf "${B}==>${N} %s\n" "$*"; }
warn() { printf "${Y}warn:${N} %s\n" "$*"; }
err()  { printf "${R}error:${N} %s\n" "$*" >&2; }
have() { command -v "$1" >/dev/null 2>&1; }

# Single-quote a value for embedding in a GENERATED script. The hooks below bake
# absolute paths in, and a home directory with a space or a quote in it would
# otherwise produce a hook that is silently syntactically broken.
quote_sh() { printf "'%s'" "$(printf '%s' "$1" | sed "s/'/'\\\\''/g")"; }

script_dir() {
  # Resolve symlinks so `ln -s .../config/stack-init.sh ~/.local/bin/stack-init`
  # still finds the repo; readlink -f is GNU — fall back to the plain path.
  local p; p="$(readlink -f "$0" 2>/dev/null || echo "$0")"
  cd "$(dirname "$p")" && pwd
}

# The contract text is NOT duplicated in this script. Both installers read the
# same two files next to them, so the POSIX and Windows variants cannot drift —
# they already had (em dashes here, hyphens there) while claiming to write the
# same managed block into the same ~/.claude/CLAUDE.md. Kept ASCII-only on
# purpose: stack-init.ps1 reads these too, and Windows PowerShell 5.1 decodes a
# BOM-less file as ANSI, which turns any non-ASCII byte into mojibake.
print_contract_file() {
  local f; f="$(script_dir)/$1"
  if [ ! -f "$f" ]; then
    err "contract source missing: $f"
    err "run stack-init from the agent-skills repo checkout (config/ ships these)"
    exit 1
  fi
  cat "$f"
}
print_contract()           { print_contract_file contract.md; }
print_contract_condensed() { print_contract_file contract-condensed.md; }

# The globally deployed skills (gauntlet-loop, opensrc, worktrunk, good-readme,
# sdd-spec).
# The three extras ship none of
# their own, and without a SKILL.md in
# $CLAUDE_DIR/skills Claude has the binaries on PATH but nothing ever surfaces
# them — the skill description is what makes the agent reach for the tool.
# Canonical copies live in skills/<name>/ in the agent-skills repo (SKILL.md
# plus any supporting files), where they work as ordinary standalone Claude
# skills; this script only DEPLOYS them, verbatim (no stack-specific text
# appended — the skills already carry their Context Stack interop notes).
# Source: the repo checkout next to this script — the script ships inside the
# repo, so run it from there (no network fallback by design). Non-fatal like
# the extras themselves.
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
  # One guard, not two: a missing directory simply yields no matches below, so
  # the found=0 branch already covers it.
  local dir="$1" f found=0
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

install_uv() {
  have uv && return
  say "  installing uv (needed to run Serena)"
  if have pacman; then sudo pacman -S --noconfirm uv || true
  else curl -LsSf https://astral.sh/uv/install.sh | sh || true; fi
  have uv || warn "uv install failed — Serena will not be able to launch"
}

# Serena runs from an ISOLATED uv tool venv, so it cannot see a system-installed
# python-gobject. Without PyGObject inside that venv, pystray silently picks its
# _xorg backend (XEmbed), which no Wayland bar hosts and which even modern X11
# panels dropped — the tray icon is then simply never drawn, with no error
# anywhere. Injecting pygobject switches pystray to _appindicator, the
# StatusNotifierItem backend every current bar does host. Best-effort: pygobject
# is a source build (needs gobject-introspection headers), and a failure just
# means the browser interface below instead of a tray.
serena_python() {
  local d rel esc
  have uv || return 1
  esc="$(printf '\033')"
  d="$(NO_COLOR=1 uv tool dir 2>/dev/null | tr -d '\r' | head -1 | sed "s/${esc}\[[0-9;]*m//g")"
  [ -n "$d" ] || return 1
  for rel in serena-agent/bin/python serena-agent/Scripts/python.exe; do
    [ -x "$d/$rel" ] && { printf '%s' "$d/$rel"; return 0; }
  done
  return 1
}

ensure_serena_tray_deps() {
  [ "$(uname -s)" = Linux ] || return 0   # macOS pystray is native (_darwin)
  local py; py="$(serena_python)" || return 0
  "$py" -c 'import gi' >/dev/null 2>&1 && return 0
  have uv || return 0
  say "  adding pygobject to serena's venv (AppIndicator tray backend)"
  # `uv pip install --python <that venv>`, NOT `uv tool install --with pygobject`.
  # The latter re-resolves serena from git and would silently UPGRADE it as a
  # side effect of a step that only means to configure a dashboard - and
  # install_global deliberately skips reinstalling a serena that is already
  # present. The cost is that `uv tool upgrade serena-agent` drops the addition;
  # that is self-healing, since the next `stack-init global` puts it back.
  uv pip install --python "$py" pygobject >/dev/null 2>&1 \
    || warn "pygobject install failed (needs gobject-introspection headers) - no serena tray icon, dashboard still reachable manually"
}

# True only when a global tray icon can ACTUALLY appear on this desktop. Both
# halves are required and neither implies the other: a bar can be hosting a
# StatusNotifier tray while pystray still resolves to a backend that cannot talk
# to it, and vice versa. Guessing from $XDG_CURRENT_DESKTOP would be wrong on
# both counts — ask the session bus and ask pystray.
serena_tray_supported() {
  local py; py="$(serena_python)" || return 1
  case "$(uname -s)" in
    Darwin) ;;
    Linux)
      have busctl || return 1
      busctl --user list 2>/dev/null | grep -q 'org\.kde\.StatusNotifierWatcher' || return 1
      ;;
    *) return 1 ;;
  esac
  # pystray binds its backend at import time; _xorg (XEmbed) and _dummy cannot
  # reach an SNI host, so anything outside this set is a dead icon.
  "$py" -c 'import pystray,sys
sys.exit(0 if pystray.Icon.__module__.rsplit(".",1)[-1] in ("_appindicator","_gtk","_darwin") else 1)' \
    >/dev/null 2>&1
}

# Sets `key: value` on a serena_config.yml key that already exists (Serena writes
# every key, commented prose plus a bare `key:` for the unset ones). Prints
# nothing; returns 0 if the file changed.
set_serena_yaml_key() {
  local cfg="$1" key="$2" val="$3"
  grep -q "^$key: *$val\$" "$cfg" && return 1
  sed -i "s|^$key:.*|$key: $val|" "$cfg"
  return 0
}

set_serena_dashboard_config() {
  # Two settings, one goal: never a dashboard window per Claude session. Serena
  # runs one instance per session, each on its own port, so open_on_launch=true
  # means a browser tab per session — the thing this turns off.
  #
  # The interface is then pinned rather than left empty. Empty means "platform
  # default", and Serena's Linux default is `browser`, which offers NO way back
  # to a dashboard once auto-open is off except typing a localhost port. When the
  # desktop can host a tray (the check above, not a guess), tray_manager gives
  # the same affordance the ps1 installer gets on Windows: ONE global icon whose
  # menu lists every running instance. When it cannot, `browser` is pinned
  # explicitly so a future change to Serena's platform default cannot quietly
  # reintroduce per-session windows.
  local cfg="$HOME/.serena/serena_config.yml" iface changed=0
  if [ ! -f "$cfg" ]; then
    say "  serena_config.yml not found (Serena writes it on first launch) — rerun global later to apply dashboard settings"
    return
  fi
  ensure_serena_tray_deps
  if serena_tray_supported; then iface=tray_manager; else iface=browser; fi
  set_serena_yaml_key "$cfg" web_dashboard_open_on_launch false && changed=1
  set_serena_yaml_key "$cfg" web_dashboard_interface "$iface" && changed=1
  if [ "$changed" = 0 ]; then
    say "  serena dashboard settings already applied (interface: $iface)"
  elif [ "$iface" = tray_manager ]; then
    say "  serena dashboard: auto-open off; tray_manager icon lists all instances"
  else
    say "  serena dashboard: auto-open off; no tray host on this desktop, so it stays"
    say "  reachable manually (ask Claude to open it, or localhost:24282)"
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
  edit_settings '
hook_cmd = sys.argv[2]
hooks = data.setdefault("hooks", {})
starts = hooks.setdefault("SessionStart", [])
if not any(h.get("command") == hook_cmd for entry in starts for h in entry.get("hooks", [])):
    starts.append({"hooks": [{"type": "command", "command": hook_cmd}]})
save()
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

install_ponytail() {
  # ponytail ships as a Claude Code plugin from a GitHub-backed marketplace.
  # `claude plugin` drives both steps non-interactively, which is the only
  # reason an installer can do this at all — the /plugin slash commands cannot
  # be scripted, and interactively they must be sent as two SEPARATE prompts.
  #
  # Non-fatal throughout (D32): ponytail is instructions, and a session without
  # them is a worse session, never a broken one.
  if ! have node; then
    warn "node not on PATH — ponytail's lifecycle hooks need it. Its skills still"
    warn "  work; the always-on activation just stays quiet instead of erroring."
    warn "  nvm/Nix users: it must be on the NON-INTERACTIVE shell's PATH."
  fi
  if claude plugin list 2>/dev/null | grep -qi ponytail; then
    say "  ponytail already installed — skipped"
    return 0
  fi
  claude plugin marketplace add DietrichGebert/ponytail >/dev/null 2>&1 \
    || warn "could not add the ponytail marketplace — skipping plugin install"
  if claude plugin install ponytail@ponytail >/dev/null 2>&1; then
    say "  ponytail installed (minimal-code ruleset injected at session start)"
  else
    warn "claude plugin install ponytail@ponytail failed — install it by hand:"
    warn "  /plugin marketplace add DietrichGebert/ponytail"
    warn "  /plugin install ponytail@ponytail      (two SEPARATE prompts)"
  fi
}

install_contract_refresh() {
  # The condensed contract was written into agent files ONLY at install time, so
  # editing contract-condensed.md left every deployed copy stale until somebody
  # re-ran the installer - the same drift D30 removed from the contract text
  # itself, reintroduced one level down. Every comparable per-repo concern had
  # already been converted to a self-healing SessionStart hook (the graph, then
  # Serena); this was the one that had not.
  #
  # Scope is ~/.claude/agents/ ONLY, deliberately. .claude/agents/ is TRACKED,
  # and a background job must never mutate files the user would have to commit
  # (the rule the graph autobuild follows by writing solely under .git/). The
  # per-repo copies stay with `init`, where a human asked for them.
  #
  # The hook reads contract-condensed.md live, through an absolute path resolved
  # now - baking the TEXT in would recreate exactly the staleness this fixes.
  local src; src="$(script_dir)/contract-condensed.md"
  mkdir -p "$CLAUDE_DIR/hooks"
  {
    cat <<'HOOK'
#!/bin/sh
# claude-context-stack: refresh the condensed routing contract in user-global
# agent files at session start. Opt out: CLAUDE_STACK_NO_CONTRACT_REFRESH=1.
# Uninstall: remove the SessionStart entry in settings.json.
[ -n "${CLAUDE_STACK_NO_CONTRACT_REFRESH:-}" ] && exit 0
HOOK
    printf 'src=%s\n' "$(quote_sh "$src")"
    printf 'dir=%s\n' "$(quote_sh "$CLAUDE_DIR/agents")"
    cat <<'HOOK'
[ -f "$src" ] || exit 0
[ -d "$dir" ] || exit 0

# Marker-guarded and sentinel-replaced, identical in shape to the installer's
# own injection: strip any existing managed block, then append the current one.
# Silent by design - a session-start hook that cannot write a file the user did
# not ask about should not editorialise about it.
for f in "$dir"/*.md; do
  [ -e "$f" ] || continue
  # Skip files already carrying the current text: the common case is no change
  # at all, and rewriting every agent file every session churns mtimes for
  # nothing.
  if grep -q '>>> claude-context-stack >>>' "$f" 2>/dev/null; then
    cur=$(awk '/>>> claude-context-stack >>>/{s=1} s{print} /<<< claude-context-stack <<</{s=0}' "$f" 2>/dev/null)
    [ "$cur" = "$(cat "$src")" ] && continue
    tmp=$(mktemp) || continue
    if awk '/>>> claude-context-stack >>>/{s=1} !s{print} /<<< claude-context-stack <<</{s=0}' \
      "$f" > "$tmp" 2>/dev/null && mv "$tmp" "$f" 2>/dev/null; then :; else rm -f "$tmp"; continue; fi
  fi
  body=$(cat "$f" 2>/dev/null) || continue
  { printf '%s\n\n' "$body"; cat "$src"; } > "$f" 2>/dev/null || continue
done
exit 0
HOOK
  } > "$CLAUDE_DIR/hooks/contract-refresh.sh"
  chmod +x "$CLAUDE_DIR/hooks/contract-refresh.sh"
  register_sessionstart_hook "bash \"$CLAUDE_DIR/hooks/contract-refresh.sh\"" >/dev/null
  say "  SessionStart contract-refresh hook installed (~/.claude/agents only; opt out: CLAUDE_STACK_NO_CONTRACT_REFRESH=1)"
}

install_global() {
  check_deps
  # Every optional install below is non-fatal on purpose. `set -e` turns both a
  # failed install AND a missing installer (exit 127) into an abort, which used
  # to take out everything after it — including the routing contract written at
  # the very end, the one step that is the whole point of the script. check_deps
  # only WARNS about cargo/pip, so "warn, then die anyway" was the old behavior.
  # One health-check pass: `claude mcp list` spawns every registered server and
  # waits on it, so calling it twice doubles the slowest step in this function.
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
  elif have uv; then
    say "  installing serena (uv tool; PyPI/dist name is serena-agent, command is serena)"
    uv tool install --from git+https://github.com/oraios/serena serena-agent \
      || warn "serena install failed — symbol routing (contract rule 2) stays unavailable"
  else warn "uv missing — cannot install serena; symbol routing (contract rule 2) stays unavailable"; fi
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
    # toolset, shell/read/file-search tools excluded. The shell exclusion is a
    # PERMISSION boundary, not a compression one (D56): Claude Code gates Bash
    # per command and MCP tools per tool, so an approved execute_shell_command
    # would be one blanket grant over every command it ever runs.
    claude mcp add --scope user serena -- serena start-mcp-server --context claude-code
    say "  serena registered at user scope (--context claude-code: no shell/read tools)"
  fi
  # Registered but NOT enabled (D53). Serena's tool manifest is a fixed
  # per-session tax whether or not a symbol tool is ever called, and it loses on
  # cheap lookups. Leaving it off makes enabling it a deliberate `/mcp` step for
  # the sessions that actually want it. Non-fatal: an older `claude` without
  # `mcp disable` just leaves it enabled, which is the pre-3.0 behaviour.
  if claude mcp disable serena >/dev/null 2>&1; then
    say "  serena DISABLED by default — enable per session with /mcp (D53)"
  else
    warn "could not disable serena (older claude?) — it will load in every session"
  fi
  # Safety net for a genuinely cold first launch (uv tool run, LSP download):
  # Claude Code's default MCP startup timeout is 30s, which is not much.
  set_global_env_var MCP_TIMEOUT 120000
  set_serena_dashboard_config

  say "serena autoinit — per-checkout project, automated (SessionStart hook)"
  install_serena_autoinit

  say "ponytail — minimal-code discipline (Claude Code plugin, default-on)"
  install_ponytail

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
  # own checkout. Every step is non-fatal: a worktrunk failure must never block
  # the stack. Bare `wt` is fine here (unlike stack-init.ps1's Windows detection):
  # brew and cargo both install the binary as plain `wt` on this platform, and
  # there is no Windows-Terminal-style collision to dodge.
  #
  # 3.0 writes NO post-start hook. It existed to replicate graphify's per-repo
  # graph and rebuild hook into each new worktree; graphify is gone (D52) and the
  # only per-checkout state left is .serena/project.yml, which serena-autoinit
  # already writes at every session start in whatever checkout you open.
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
    # Remove the graphify post-start hook a pre-3.0 install wrote, if it is ours.
    WT_CFG="${XDG_CONFIG_HOME:-$HOME/.config}/worktrunk/config.toml"
    if [ -f "$WT_CFG" ] && grep -q 'claude-context-stack' "$WT_CFG"; then
      tmp="$(mktemp)"
      awk '/^# claude-context-stack: replicate/{s=1} s&&/^claude-context-stack = /{s=0;next} !s' \
        "$WT_CFG" > "$tmp" && mv "$tmp" "$WT_CFG"
      say "  removed obsolete graphify post-start hook from $WT_CFG (D52)"
    fi
  else
    warn "worktrunk unavailable — parallel-worktree support skipped (stack unaffected)"
  fi

  say "Global skills -> $CLAUDE_DIR/skills (gauntlet-loop, opensrc, worktrunk, good-readme, sdd-spec)"
  # Deployed unconditionally (even if a binary install above failed — both are
  # global tools the user may add later, and the worktrunk skill itself covers
  # offering the install) and idempotently: overwritten every run, like the
  # contract. See install_extra_skill for source resolution.
  install_extra_skill gauntlet-loop
  install_extra_skill opensrc
  install_extra_skill worktrunk
  # Surface no binary — global because they are project-agnostic (D58, D59).
  install_extra_skill good-readme
  install_extra_skill sdd-spec

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
  # ...and keep them current between installs. Only the user-global copies:
  # .claude/agents/ is tracked, so it stays with `init` (see the function).
  install_contract_refresh

  have rust-analyzer || warn "rust-analyzer not on PATH — Serena needs it for Rust (rustup component add rust-analyzer)"
  echo; say "Global install done. No new shell needed and no per-repo step."
  say "Serena is registered but OFF — enable it per session with /mcp (D53)."
  say "ponytail is on by default; run '$(basename "$0") verify' to confirm both."
}

# Per-repo skill deployment (`skills`). The global install deploys only the
# project-agnostic skills (gauntlet-loop, opensrc, worktrunk, good-readme,
# sdd-spec);
# the repo's DOMAIN skills (architecture-blueprint, rust-type-driven,
# rust-bevy-architecture, rust-wgpu-functional, macro-analyst,
# security-vuln-gauntlet) stay out of
# $CLAUDE_DIR/skills on purpose: every skill there pays its description into
# EVERY session's context, in every project, relevant or not — about a
# thousand tokens of standing overhead for skills that only apply to specific
# project types, plus the odd spurious trigger. This deploys them into the
# CURRENT repo's .claude/skills/ instead, where only sessions in that repo
# pay for them.
#
# Symlink by default, copy on --copy. A symlink stays current with this
# checkout automatically — the same reasoning that turned the condensed
# contract into a refresh hook (D43: install-time copies go stale). But its
# target is an absolute path on THIS machine, so it must never be committed;
# the path goes into .git/info/exclude (the machine-local channel the
# SessionStart hooks already use). --copy inverts the trade: committable and
# portable to collaborators, refreshed only by re-running, and taken OUT of
# the exclude so git can track it. Copies carry a marker file so a refresh
# only ever deletes a directory this command created — a user's own
# same-named skill is refused, never clobbered.
SKILL_COPY_MARKER=".claude-context-stack"

repo_skill_names() {
  local d
  for d in "$(script_dir)/../skills"/*/; do
    [ -f "${d}SKILL.md" ] && basename "$d"
  done
}

list_repo_skills() {
  local top="" name state dst
  in_git_repo && top="$(git rev-parse --show-toplevel 2>/dev/null)"
  say "deployable skills (canonical: $(script_dir)/../skills)"
  for name in $(repo_skill_names); do
    state=""
    [ -f "$CLAUDE_DIR/skills/$name/SKILL.md" ] && state="global"
    if [ -n "$top" ]; then
      dst="$top/.claude/skills/$name"
      if [ -L "$dst" ]; then state="${state:+$state, }linked here"
      elif [ -d "$dst" ]; then state="${state:+$state, }copied here"; fi
    fi
    row "$name" "${state:-not deployed}"
  done
  [ -n "$top" ] || say "  (not in a git repo — per-repo state not shown)"
}

# Exact-line add/remove on the COMMON git dir's info/exclude, so one entry
# covers the main checkout and every linked worktree (same rule the hooks
# follow). Exact-match (-xF) on both sides: these must never eat a broader
# user-written pattern that merely contains the same text.
exclude_line_add() {
  local cgd="$1" line="$2"
  mkdir -p "$cgd/info"
  grep -qxF "$line" "$cgd/info/exclude" 2>/dev/null || printf '%s\n' "$line" >> "$cgd/info/exclude"
}
exclude_line_remove() {
  local cgd="$1" line="$2" tmp
  [ -f "$cgd/info/exclude" ] || return 0
  grep -qxF "$line" "$cgd/info/exclude" || return 0
  tmp="$(mktemp)" || return 0
  if grep -vxF "$line" "$cgd/info/exclude" > "$tmp"; then mv "$tmp" "$cgd/info/exclude"
  else rm -f "$tmp"; fi
}

deploy_repo_skills() {
  local mode=link names="" a name src dst top cgd line fail=0
  for a in "$@"; do
    case "$a" in
      --copy) mode=copy ;;
      -*) err "unknown flag: $a"
          echo "usage: $(basename "$0") skills [--copy] [<name>...]"; exit 1 ;;
      *) names="$names $a" ;;
    esac
  done
  if [ -z "${names// /}" ]; then list_repo_skills; return 0; fi
  in_git_repo || { err "run from a git repo — skills deploy into the repo's .claude/skills/"; exit 1; }
  top="$(git rev-parse --show-toplevel 2>/dev/null)"
  [ -n "$top" ] || { err "could not resolve the repo root"; exit 1; }
  cgd="$(cd "$top" && { git rev-parse --git-common-dir 2>/dev/null || git rev-parse --git-dir; })"
  case "$cgd" in /*) ;; *) cgd="$top/$cgd" ;; esac
  mkdir -p "$top/.claude/skills"
  for name in $names; do
    src="$(script_dir)/../skills/$name"
    if [ ! -f "$src/SKILL.md" ]; then
      err "no such skill: $name (available: $(repo_skill_names | tr '\n' ' '))"
      fail=1; continue
    fi
    # Absolute and symlink-resolved: a link target relative to cwd would break
    # the moment anyone ran this from a different directory.
    src="$(CDPATH= cd -- "$src" && pwd -P)"
    dst="$top/.claude/skills/$name"
    # No trailing slash: a slash-terminated gitignore pattern matches only real
    # directories, and the default deployment is a SYMLINK — which git treats
    # as a file, so the slashed form silently failed to exclude it.
    line="/.claude/skills/$name"
    if [ -e "$dst" ] && [ ! -L "$dst" ] && [ ! -f "$dst/$SKILL_COPY_MARKER" ]; then
      warn "$name: $dst exists and was not deployed by this command — remove it yourself first"
      fail=1; continue
    fi
    if [ "$mode" = link ]; then
      # A previous --copy of ours upgrades to a link; rm -rf on a symlink
      # removes the link itself, never the target.
      [ -d "$dst" ] && [ ! -L "$dst" ] && rm -rf "$dst"
      ln -sfn "$src" "$dst"
      exclude_line_add "$cgd" "$line"
      say "  $name linked -> $src (machine-local; excluded from git)"
    else
      rm -rf "$dst"
      cp -R "$src" "$dst"
      printf '%s\n' "Deployed by stack-init skills --copy. Managed: re-running replaces this directory; hand edits do not survive." > "$dst/$SKILL_COPY_MARKER"
      exclude_line_remove "$cgd" "$line"
      say "  $name copied (committable; re-run 'skills --copy $name' to refresh)"
    fi
  done
  say "skills load at session start — restart Claude Code to pick them up"
  [ "$fail" = 0 ] || exit 1
}

# One aligned printf for every verify line. The hand-spaced echo pairs it
# replaces spelled each label twice (once per branch) and had drifted to three
# different column widths, so adding a longer label silently misaligned a row.
row()      { printf '  %-17s %s\n' "$1:" "$2"; }
row_have() { if have "$1"; then row "$2" "$3"; else row "$2" "$4"; fi; }
row_skill() {
  if [ -f "$CLAUDE_DIR/skills/$1/SKILL.md" ]; then row "$1 skill" "OK (global)"
  else row "$1 skill" "NOT deployed — rerun global"; fi
}
row_hook() {
  # A SessionStart hook counts as wired only when BOTH the script exists and
  # settings.json references it — either half alone is a half-install.
  if [ -x "$CLAUDE_DIR/hooks/$1.sh" ] && grep -q "$1" "$CLAUDE_DIR/settings.json" 2>/dev/null
  then row "$2" "OK (SessionStart)"; else row "$2" "NOT registered"; fi
}

verify() {
  say "verifying"
  if claude mcp list 2>/dev/null | grep -qi serena; then row "serena (mcp)" "OK (user scope)"
  else row "serena (mcp)" "NOT registered"; fi
  # Registered-but-disabled is the INTENDED state (D53), so report it as OK and
  # flag the enabled case instead — the opposite of every other row here.
  if claude mcp list 2>/dev/null | grep -i serena | grep -qi 'disabled'; then
    row "serena state" "OK (disabled by default — /mcp to enable per session)"
  else row "serena state" "ENABLED globally — D53 expects it off"; fi
  if claude plugin list 2>/dev/null | grep -qi ponytail
  then row ponytail "OK (plugin installed)"
  else row ponytail "NOT installed — run: claude plugin install ponytail@ponytail"; fi
  # Serena retention gate (D57). serena/tools/tools_base.py logs
  # "<tool>: {params}; session_id: <id>" on every execution, so the "; session_id:"
  # suffix separates a REAL call from the tool name merely appearing in a startup
  # manifest line. Reported on every verify so the gate collects itself rather
  # than waiting for someone to remember to look (the defect that sank D20).
  if [ -d "$HOME/.serena/logs" ]; then
    # `|| true` is load-bearing under `set -euo pipefail`: grep exits 1 when it
    # finds nothing, pipefail propagates that through the pipe, and set -e then
    # aborts verify at the FIRST run on a machine where Serena was never used -
    # which is exactly the machine this row exists to report on.
    _sact="$( { grep -rl 'activate_project: .*session_id:' "$HOME/.serena/logs" 2>/dev/null || true; } | wc -l | tr -d ' ')"
    if [ "$_sact" -gt 0 ]
    then row "serena used" "OK ($_sact session(s) activated it — D57 gate satisfied)"
    else row "serena used" "NEVER activated — if still 0 after ~10 sessions, remove it (D57, B7)"; fi
  fi
  # ponytail's hooks are Node; without node the activation goes quiet rather
  # than erroring, so a broken install is invisible from inside a session.
  row_have node "node" "OK (ponytail hooks)" "MISSING — ponytail activation stays silent"
  row_hook serena-autoinit "serena autoinit"
  row_hook contract-refresh "contract refresh"
  if have wt || have git-wt; then row worktrunk "OK (workflow tool — outside the contract)"
  else row worktrunk "NOT installed (optional)"; fi
  row_have opensrc "opensrc" "OK (context tool — outside the contract)" "NOT installed (optional)"
  row_skill opensrc
  row_skill worktrunk
  row_skill gauntlet-loop
  row_skill good-readme
  row_skill sdd-spec
  if grep -q '>>> claude-context-stack >>>' "$CLAUDE_MD" 2>/dev/null
  then row contract "OK ($CLAUDE_MD)"; else row contract "MISSING"; fi
  if in_git_repo; then
    # Everything below is PER CHECKOUT, and a linked worktree is a checkout like
    # any other: it gets its own Serena project, because that describes the code
    # at THIS path.
    local gd cgd br refresh_hook
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
      row checkout "linked worktree ($br) — own Serena project"
    else row checkout "primary"; fi
    # Anchor on the repo ROOT, never cwd: .serena/ is written at the top level
    # by the SessionStart hook (which `cd "$top"` first), so cwd-relative tests
    # reported "none" for a fully wired repo whenever verify ran from a subdir.
    local top
    top="$(git rev-parse --show-toplevel 2>/dev/null)" || top=""
    [ -n "$top" ] || top="$PWD"
    if [ -f "$top/.serena/project.yml" ]
    then row "serena project" "OK (.serena/project.yml)"
    else row "serena project" "none — autoinits next session"; fi
    # Repo-local skills deployed by `skills` (or by hand — anything with a
    # SKILL.md counts, annotated by how it got here).
    local rskills="" sd
    for sd in "$top/.claude/skills"/*/; do
      [ -f "${sd}SKILL.md" ] || continue
      if [ -L "${sd%/}" ]; then rskills="$rskills $(basename "$sd")(link)"
      else rskills="$rskills $(basename "$sd")(copy)"; fi
    done
    if [ -n "$rskills" ]; then row "repo skills" "${rskills# }"
    else row "repo skills" "none (optional — deploy: $(basename "$0") skills <name>)"; fi
    # 3.0 installs NO git hooks: the four graph-refresh hooks went with graphify
    # (D52). Report any the stack left behind so an upgraded machine can be
    # cleaned, rather than silently leaving dead hooks in every repo.
    local hooks_dir stale=""
    hooks_dir="$(get_git_hooks_dir)"
    [ -n "$hooks_dir" ] || hooks_dir=".git/hooks"
    for refresh_hook in post-commit post-checkout post-merge post-rewrite; do
      grep -q 'claude-context-stack:' "$hooks_dir/$refresh_hook" 2>/dev/null \
        && stale="$stale $refresh_hook"
    done
    if [ -n "$stale" ]; then row "stale hooks" "pre-3.0 graph hooks present:${stale} (safe to delete)"
    else row "git hooks" "OK (none — 3.0 installs no git hooks)"; fi
  fi
}

verify_docs() {
  # Reinstated after being declined. The stated reason for removing it - "a third
  # implementation language" - was wrong on this platform: python3 is already a
  # hard prerequisite (check_deps aborts without it) and already runs every
  # settings.json merge and `stats`. It is right on Windows, where the .ps1 uses
  # PowerShell for the same work, which is why this subcommand is Unix-only and
  # deliberately NOT mirrored - it validates the REPO's documentation, not a
  # user's installation, so a Windows user never has occasion to run it.
  #
  # Only the two purely textual checks came back. The third - tool subcommands
  # named in the docs against that tool's --help - stays dropped: it needs the
  # tools installed, it is slow, and it has one hit in the project's history.
  local root; root="$(script_dir)"
  have python3 || { err "python3 not found - cannot run verify --docs"; return 1; }
  python3 - "$root" <<'PYEOF'
import os, re, sys

root = sys.argv[1]
SPEC = 'claude-code-context-stack.md'
DEC = 'DECISIONS.md'
DOCS = [SPEC, DEC, 'README.md', 'CHANGELOG.md', 'BACKLOG.md',
        'contract.md', 'contract-condensed.md']


def read(name):
    path = os.path.join(root, name)
    if not os.path.isfile(path):
        return None
    with open(path, encoding='utf-8') as fh:
        return fh.read()


spec = read(SPEC) or ''
# '## 7. Guardrails', '### 2.1 graphify', '### 6.x Subagents' -> 7, 2.1, 6.x.
# A bare '2' is valid whenever '## 2.' exists, which is how the spec numbers its
# top-level sections, so no extra work is needed to accept '2.4' AND '2'.
sections = set(re.findall(r'^#{2,3}\s+(\d+(?:\.\w+)?)\.?\s', spec, re.M))
decisions = set(re.findall(r'^##\s+D(\d+)\b', read(DEC) or '', re.M))

if not sections or not decisions:
    sys.stderr.write('verify --docs: could not read the doc set at %s\n' % root)
    sys.exit(1)

# Ranges are written with an en dash in this doc set ('Read S1-3 first'), so the
# tail of a range has to be validated too, not just the head.
SECTION_REF = re.compile(u'§\\s*(\\d+(?:\\.\\w+)?)'
                         u'(?:\\s*[–—-]\\s*(\\d+(?:\\.\\w+)?))?')
DECISION_REF = re.compile(r'\bD(\d+)\b')

bad = []
for name in DOCS:
    text = read(name)
    if text is None:
        continue
    def at(pos):
        return text.count('\n', 0, pos) + 1
    # DECISIONS.md is exempt from the section check, and not as a convenience.
    # Its bodies are append-only, and D36 renumbered the spec - so an old entry
    # citing a section that no longer exists is both CORRECT (it describes the
    # numbering of its own time) and unfixable (the body may not be rewritten).
    # A check that reports defects nobody is permitted to repair produces
    # permanent noise, and a checker people learn to ignore is worse than none.
    # Decision citations are still checked here: those must always resolve.
    if name != DEC:
        for m in SECTION_REF.finditer(text):
            for ref in (m.group(1), m.group(2)):
                if ref and ref not in sections:
                    bad.append(u'%s:%d: no such section: §%s' % (name, at(m.start()), ref))
    for m in DECISION_REF.finditer(text):
        if m.group(1) not in decisions:
            bad.append('%s:%d: no such decision: D%s' % (name, at(m.start()), m.group(1)))

for line in bad:
    print(line)
print('  %d sections, %d decisions, %d files checked -- %s'
      % (len(sections), len(decisions), len([d for d in DOCS if read(d) is not None]),
         'OK' if not bad else '%d BROKEN REFERENCE(S)' % len(bad)))
sys.exit(1 if bad else 0)
PYEOF
}

case "${1:-global}" in
  global|"")  install_global ;;
  skills)     shift; deploy_repo_skills "$@" ;;
  # Not `[ ... ] && verify_docs || verify`: that idiom runs the full install
  # check as a "fallback" the moment --docs legitimately reports a broken
  # reference and exits non-zero.
  verify)     if [ "${2:-}" = "--docs" ]; then verify_docs; else verify; fi ;;
  contract)   [ "${2:-}" = "--condensed" ] && print_contract_condensed || print_contract ;;
  # Print the whole comment banner, however long it grows. The old fixed
  # '2,57p' range silently truncated it mid-sentence once the header moved -
  # by the time this was noticed it was cutting the PREREQS line off.
  -h|--help|help) awk 'NR==1{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "$0" ;;
  *) err "unknown command: $1"; echo "usage: $(basename "$0") [global|skills [--copy] [<name>...]|verify [--docs]|contract [--condensed]|help]"; exit 1 ;;
esac

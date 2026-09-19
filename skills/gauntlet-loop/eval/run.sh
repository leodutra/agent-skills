#!/usr/bin/env bash
# Run the write-mode cases through `claude -p` (flags: harness-claude-code.md, S7) and check them.
# run.sh [--upto N] [--only id,id] [--skill-only] [--baseline]   --skill-only runs where references/ does not exist: SKILL.md alone must do.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"; skill="$(dirname "$here")"; root="$skill"
upto=()
while [ $# -gt 0 ]; do case "$1" in
  --upto) upto+=(--upto "$2"); shift 2;;
  --only) upto+=(--only "$2"); shift 2;;
  --baseline) upto+=(--baseline); shift;;
  --skill-only) root="$(mktemp -d)"; mkdir -p "$root/eval/write-mode"; cp -R "$here/write-mode/fixtures" "$root/eval/write-mode/"; shift;;
  *) echo "unknown: $1" >&2; exit 2;; esac; done
out="${GAUNTLET_EVAL_OUT:-$(mktemp -d)}"; mkdir -p "$out"
one() {
  (cd "$root" && claude -p "$(python3 "$here/check.py" --field "$1" goal)" \
     --append-system-prompt "$(cat "$skill/SKILL.md")" --tools Read --setting-sources "" --strict-mcp-config \
     --model "$(python3 "$here/check.py" --field "$1" model)" --output-format json < /dev/null > "$out/$1.json" 2> "$out/$1.err") || true
}
export -f one; export here skill root out
python3 "$here/check.py" --list "${upto[@]/--baseline/}" | xargs -P 4 -I{} bash -c 'one {}'
python3 "$here/check.py" "${upto[@]}" "$out"

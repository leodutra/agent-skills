#!/usr/bin/env bash
# Run the reader definition on every frozen pair in both orders (flags: harness-claude-code.md, S7) and check the verdicts.
# run_critic.sh [--only domain[/pair-N]] [--baseline]
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"; skill="$(dirname "$here")"; only=""; check=()
while [ $# -gt 0 ]; do case "$1" in --only) only="$2"; shift 2;; --baseline) check+=(--baseline); shift;; *) echo "unknown: $1" >&2; exit 2;; esac; done
out="${GAUNTLET_EVAL_OUT:-$(mktemp -d)}"; mkdir -p "$out"
model="${GAUNTLET_EVAL_CRITIC_MODEL:-$(python3 -c "import json;print(json.load(open('$here/critic/suite.json'))['model'])")}"
one() { # $1 = domain/pair-N, $2 = ab | ba
  local src="$here/critic/$1" id; id="$(echo "$1" | tr / -)-$2"
  local proj; proj="$(mktemp -d)"; local pair="$proj/.gauntlet/pairs/$id"
  mkdir -p "$proj/.claude/agents" "$pair"
  sed "s/^model: .*/model: $model/" "$skill/agents/reader.md" > "$proj/.claude/agents/reader.md"   # the body is what is under test
  if [ "$2" = ab ]; then cp -R "$src/better" "$pair/a"; cp -R "$src/worse" "$pair/b"; else cp -R "$src/worse" "$pair/a"; cp -R "$src/better" "$pair/b"; fi
  [ -d "$src/shared" ] && cp -R "$src/shared/." "$pair/"
  cp "$src/PROMPT.md" "$pair/PROMPT.md"; echo "$id" > "$pair/PAIR_ID"
  (cd "$proj" && claude -p "$pair" --agent reader --setting-sources project --strict-mcp-config \
     --allowedTools "Read Glob Grep Bash" --output-format json < /dev/null > "$out/$id.json" 2> "$out/$id.err") || true
  rm -rf "$proj"
}
export -f one; export here skill out model
find "$here/critic" -name kind | sed -e "s#^$here/critic/##" -e 's#/kind$##' | sort | { [ -n "$only" ] && grep "^$only" || cat; } \
  | while read -r p; do echo "$p ab"; echo "$p ba"; done | xargs -P 6 -L 1 bash -c 'one "$0" "$1"'
python3 "$here/check_critic.py" "${check[@]}" ${only:+--only "$only"} "$out"

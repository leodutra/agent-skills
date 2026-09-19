#!/usr/bin/env bash
# Harness tokens belong in references/harness-claude-code.md and the Portability section of what-breaks.md, nowhere else.
# SKILL.md keeps exactly two, `/goal` and `/effort xhigh`: the paste prompt and the line under it are harness text by design.
set -euo pipefail
skill="$(cd "$(dirname "$0")/.." && pwd)"; fail=0
tokens='/goal|/loop|/effort|/sandbox|ultracode|SendMessage|CLAUDE_CODE_|subagent_type|isolation: worktree|Agent tool|Workflow tool|Artifact tool|as an Artifact|PreToolUse|SubagentStart|SubagentStop|settings\.json|omitClaudeMd|maxTurns|claude -p|worktrunk|\bwt (switch|list|merge|remove)\b'
scan() { # $1 file, stdin its text with the allowed parts already removed
  local hits; hits=$(grep -nE "$tokens" || true)
  if [ -n "$hits" ]; then echo "FAIL  $1"; echo "$hits" | sed 's/^/        /'; fail=1; else echo "ok    $1"; fi; }
sed -e 's#`/goal`##g' -e 's#`/effort xhigh`##g' -e 's#^/goal ##' "$skill/SKILL.md" | scan SKILL.md
for f in "$skill"/references/*.md "$skill"/references/domains/*.md; do
  case "$(basename "$f")" in
    harness-claude-code.md) ;;
    what-breaks.md) sed '/^## Portability/,/^## /d' "$f" | scan "references/what-breaks.md (outside Portability)" ;;
    example-run.md) sed -e 's#^/goal ##' "$f" | scan "references/example-run.md (first word of the pasted prompt aside)" ;;
    *) scan "${f#"$skill"/}" < "$f" ;;
  esac
done
exit $fail

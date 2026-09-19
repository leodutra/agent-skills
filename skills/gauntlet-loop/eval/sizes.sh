#!/usr/bin/env bash
# Byte ceilings from the spec's size table, and the two-line description. Free; runs on every commit and in CI.
set -euo pipefail
skill="$(cd "$(dirname "$0")/.." && pwd)"; fail=0
check() { local n; n=$(wc -c < "$skill/$1"); if [ "$n" -gt "$2" ]; then echo "FAIL  $1: $n bytes > $2"; fail=1; else echo "ok    $1: $n bytes <= $2"; fi; }
check SKILL.md 7000
check references/running-the-loop.md 10239
check references/controller.md 6000
lines=$(awk '/^---$/{n++; next} n==1 && /^description:/{d=1} n==1 && d{c++} n==2{exit} END{print c}' "$skill/SKILL.md")
if [ "$lines" -gt 2 ]; then echo "FAIL  SKILL.md description: $lines lines > 2"; fail=1; else echo "ok    SKILL.md description: $lines lines"; fi
# Write mode's default loaded text is under half of the baseline's 16,030 + ~3,700 bytes. The baseline's flow read a
# domain file; this one does not (spec A11), so the default load is SKILL.md. The second line is for the reader who does.
loaded=$(wc -c < "$skill/SKILL.md")
if [ "$loaded" -ge 9865 ]; then echo "FAIL  write mode loads $loaded bytes >= 9865"; fail=1; else echo "ok    write mode loads $loaded bytes < 9865 (half the baseline)"; fi
domain=$(cat "$skill"/references/domains/*.md | wc -c); files=$(ls "$skill"/references/domains/*.md | wc -l)
echo "info  with one domain file of average size: $(( loaded + domain / files )) bytes (the baseline: 19730)"
exit $fail

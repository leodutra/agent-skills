#!/usr/bin/env python3
"""Every rule in fundamentals.md reaches its home, and nothing in the lints or SKILL.md lacks a rule.

trace-ledger.md has one row per fundamentals.md ID: `| ID | home | holds | note |`.
- home `lint`: holds names lints (`unsafe_code`, `clippy::unwrap_used`), clippy.toml entries
  (`disallowed-methods std::process::abort`, `config allow-unwrap-in-tests`) or `level deny`.
- home `skill`: holds quotes SKILL.md (`"…"`, whitespace-insensitive).
- home `lint+skill`: both; the note says why the model needs it before linting.
An optional fifth cell, `eval`, names the files that prove the rule: `judgment:<dir>/<file>` (tier 3),
`doctest:<path>#<fragment>` (tier 2, from this directory; the fragment, a piece of the doctest
that proves this rule, must appear in the file) or `lints:<path>` (a tier 1 sample). Every S rule needs
one; every tier 3 sample must be named by some row.
`;` separates items. Fails when an ID is in one of fundamentals.md and the ledger only; a lint item,
config entry or quote doesn't exist; a lints.toml lint, clippy.toml entry or SKILL.md paragraph or
sentence is held by no row (sentences, so one quote never covers a whole bullet). No cargo, no model calls.
"""
import re
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parent.parent / "skills" / "rust-style-guide"
SKILL = SKILL_DIR / "SKILL.md"
FUNDAMENTALS = SKILL_DIR / "references" / "fundamentals.md"
LEDGER = HERE / "trace-ledger.md"
norm = lambda s: " ".join(s.split())


def skill_units(text):
    """SKILL.md's paragraphs and list items, outside the front matter, headings and code blocks."""
    text = re.sub(r"(?s)\A---\n.*?\n---\n", "", text)
    text = re.sub(r"(?ms)^```.*?^```\n?", "\n", text)
    units, current = [], []
    for line in text.splitlines():
        starts_item = re.match(r"\s*(?:[-*]|\d+\.) ", line)
        if not line.strip() or line.startswith("#") or starts_item:
            if current:
                units.append(norm(" ".join(current)))
            current = [] if not line.strip() or line.startswith("#") else [line]
        else:
            current.append(line)
    if current:
        units.append(norm(" ".join(current)))
    # One sentence at a time, so a sentence added to a covered bullet needs its own fundamental. Code
    # spans are masked while splitting, so a `.` inside backticks never ends a sentence.
    sentences = []
    for unit in units:
        spans = iter(re.findall(r"`[^`]*`", unit))
        masked = re.sub(r"`[^`]*`", "\0", unit)
        for part in re.split(r"(?<=[.!?])\s+(?=[A-Z*(\0])", masked):
            sentences.append(re.sub("\0", lambda _: next(spans), part))
    return [s for s in sentences if len(s.split()) > 3]  # a bare "**Write**" lead-in is no rule


def main():
    problems = []
    fundamentals_ids = set(re.findall(r"\b([LSM]\d+)\b", " ".join(
        m for m in re.findall(r"\(((?:[LSM]\d+)(?:, [LSM]\d+)*)\)", FUNDAMENTALS.read_text()))))
    lints = tomllib.loads((SKILL_DIR / "assets" / "lints.toml").read_text())["lints"]
    config = tomllib.loads((SKILL_DIR / "assets" / "clippy.toml").read_text())
    lint_names = set(lints["rust"]) | {f"clippy::{n}" for n in lints["clippy"]}
    entries = {f"{k} {e['path']}" for k in ("disallowed-types", "disallowed-methods", "disallowed-macros")
               for e in config.get(k, [])}
    entries |= {f"config {k}" for k, v in config.items() if not isinstance(v, list)}
    skill = SKILL.read_text()
    skill_norm = norm(skill)

    rows = {}
    for line in LEDGER.read_text().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) not in (4, 5) or not re.fullmatch(r"[LSM]\d+", cells[0]):
            continue
        if cells[0] in rows:
            problems.append(f"{cells[0]}: two ledger rows")
        rows[cells[0]] = cells + [""] * (5 - len(cells))

    held_lints, quotes, proven = set(), [], set()
    roots = {"judgment": HERE / "rules" / "judgment", "doctest": HERE, "lints": HERE / "rules" / "lints"}
    for rid, home, holds, note, evals in rows.values():
        refs = [e.strip() for e in evals.split(";") if e.strip()]
        if rid[0] == "S" and not refs:
            problems.append(f"{rid}: skill rule with no eval")
        for ref in refs:
            kind, _, path = ref.partition(":")
            path, _, fragment = path.partition("#")
            target = roots[kind] / path if kind in roots else None
            if not target or not target.is_file():
                problems.append(f"{rid}: eval {ref!r} doesn't exist")
            elif kind == "doctest" and (not fragment or fragment not in target.read_text()):
                problems.append(f"{rid}: eval {ref!r} names no doctest fragment found in the file")
            else:
                proven.add(target.resolve())
        items = [i.strip() for i in holds.split(";") if i.strip()]
        said = [i[1:-1] for i in items if i.startswith('"') and i.endswith('"')]
        named = [i for i in items if not (i.startswith('"') and i.endswith('"'))]
        want = {"L": ("lint", "lint+skill"), "S": ("skill",), "M": ("skill",)}[rid[0]]
        if home not in want:
            problems.append(f"{rid}: home {home!r}, but an {rid[0]} ID lives in {' or '.join(want)}")
        if "lint" in home and not named:
            problems.append(f"{rid}: home {home} holds no lint")
        if "skill" in home and not said:
            problems.append(f"{rid}: home {home} quotes nothing from SKILL.md")
        if home == "lint" and said or home == "skill" and named:
            problems.append(f"{rid}: holds items outside its home {home}")
        if home == "lint+skill" and not note:
            problems.append(f"{rid}: restated in SKILL.md without saying why it's needed before linting")
        for item in named:
            if item == "level deny":
                continue
            if item not in lint_names | entries:
                problems.append(f"{rid}: {item!r} is not in lints.toml or clippy.toml")
            held_lints.add(item)
        for quote in said:
            if norm(quote) not in skill_norm:
                problems.append(f"{rid}: SKILL.md doesn't say {quote!r}")
            quotes.append(norm(quote))

    samples = {f.resolve() for f in roots["judgment"].rglob("*") if f.is_file() and f.name != "rule.md"
               and ".claude" not in f.parts}
    problems += [f"{f.relative_to(roots['judgment'].resolve())}: tier 3 sample no rule names as its eval"
                 for f in sorted(samples - proven)]
    problems += [f"{i}: tagged in fundamentals.md, no ledger row" for i in sorted(fundamentals_ids - rows.keys())]
    problems += [f"{i}: ledger row, not tagged in fundamentals.md" for i in sorted(rows.keys() - fundamentals_ids)]
    problems += [f"{x}: in the lint set, no fundamental holds it" for x in sorted((lint_names | entries) - held_lints)]
    problems += [f"SKILL.md says, with no fundamental: {u[:110]!r}" for u in skill_units(skill)
                 if not any(q in u for q in quotes)]
    if problems:
        print("FAIL\n" + "\n".join(f"- {p}" for p in problems))
        return 1
    homes = [r[1] for r in rows.values()]
    print(f"ok ({len(rows)} fundamentals: {homes.count('lint')} lint, {homes.count('skill')} skill, "
          f"{homes.count('lint+skill')} both; every lint entry and SKILL.md sentence has one; {sum(1 for r in rows.values() if r[4])} have evals)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

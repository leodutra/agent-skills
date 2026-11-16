#!/usr/bin/env python3
"""Tier 3 of the per-rule suite: the guide's judgment rules, the ones no lint holds.

rules/judgment/<rule>/ holds rule.md (the guide's wording and one yes/no question), bad*.rs (breaks
it), good*.rs (the guide's way) and allowed-*.rs (an Allowed entry the rule tempts a reader to flag;
an optional first line, `// keep: <what>`, names a construct a fix must not remove, and is stripped
before any model sees the file).

  python3 rules.py                  static, no model calls: every sample compiles and passes the lint
                                    set (a bad sample a lint catches belongs in tier 1, not here)
  python3 rules.py --judgment       one grading call per sample: the rule's grader must flag every
                                    bad sample and no good or allowed one
  python3 rules.py --fix            per bad and allowed sample, a skill arm and a no-skill arm each
                                    get "fix what needs fixing" and reply with the file; the same
                                    grader judges the result, an allowed construct must survive, and
                                    the lint set's verdict on the result is reported apart
  --rules a,b  --only rule/file,...  --arms skill,none  --model sonnet  -j 4  --dry-run (prints the calls and a token
  estimate, spends nothing). `--fix --arms none` screens: a rule the bare model already fixes can't
  show what the skill adds, so it leaves the model eval.

The model modes spend the user's claude.ai usage and need the API, which the sandbox blocks.
Results: .bench/rsg-rules-<time>/results.json, with every reply.
"""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re
import sys
import tempfile
import time

from claude_cli import claude
from static_eval import ASSETS, clippy, member

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
JUDGMENT = HERE / "rules" / "judgment"
WORK = Path(tempfile.gettempdir()) / "rsg-rules"
DEPS = """
thiserror = "2"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
tokio = { version = "1", features = ["io-util", "macros", "sync"] }
"""
# Rough input tokens per call (2026-11-15 bench: a review run ~18k, a grading call ~7k; these are smaller).
EST = {"grade": 3_000, "fix-skill": 4_500, "fix-none": 4_000, "skill-cache-write": 6_000}  # fresh input; 2026-11-16 screen
GRADER_SYSTEM = "You check Rust code against one rule of a style guide and reply with JSON only."


def samples(rules):
    for rule in rules:
        for f in sorted((JUDGMENT / rule).glob("*.rs")):
            kind = "allowed" if f.name.startswith("allowed") else "bad" if f.name.startswith("bad") else "good"
            yield rule, kind, f


def code_and_keep(path):
    text = path.read_text()
    keep = re.match(r"// keep: (.*)\n", text)
    return (text[keep.end():], keep[1]) if keep else (text, None)


def keep_of(path):
    """An allowed sample's `// keep:` construct, if it must survive a fix; without one, an allowed
    sample only must not be flagged (moving to the guide's default form is no over-fix)."""
    return code_and_keep(path)[1]


def module(rule, path):
    return re.sub(r"\W", "_", f"{rule}_{path.stem}")


def lint_check(sources):
    """{name: source} → {name: (status, diagnostics)}, and diagnostics no file explains.

    Each source is its own crate (one workspace: one lockfile, one target dir), so a file that doesn't
    compile can't stop the lint pass on the others. Status: `clean` only when cargo finished checking
    the crate and its tests with no diagnostic; `broken` on a compile error; `lints` on lint findings;
    `unknown` when cargo never got to it."""
    lints = (ASSETS / "lints.toml").read_text()
    for old in WORK.glob("*/Cargo.toml") if WORK.exists() else []:
        if old.parent.name not in sources:
            old.unlink()
    for name, source in sources.items():
        member(WORK, name, lints, DEPS)
        (WORK / name / "src" / "lib.rs").write_text(source)
    (WORK / "Cargo.toml").write_text(f'[workspace]\nresolver = "3"\nmembers = {json.dumps(sorted(sources))}\n')
    (WORK / "clippy.toml").write_text((ASSETS / "clippy.toml").read_text())
    seen, stray, checked = clippy(WORK)
    files = {str((WORK / name / "src" / "lib.rs").resolve()): name for name in sources}
    result = {}
    for file, name in files.items():
        diags = sorted(seen.get(file, set()))
        if any(re.fullmatch(r"E\d{4}", code) for code, _ in diags):
            status = "broken"
        elif diags:
            status = "lints"
        elif {(name, False), (name, True)} <= checked:
            status = "clean"
        else:
            status = "unknown"
        result[name] = (status, diags)
    stray += [f"{file}: {sorted(diags)}" for file, diags in seen.items() if file not in files]
    return result, stray


def grade(rule, code, keep, model, dry_run):
    question = (JUDGMENT / rule / "rule.md").read_text().strip()
    extra = (f'\n\nAlso say whether the code still has {keep}: "kept": true|false.' if keep else "")
    prompt = (f"The rule:\n\n{question}\n\nThe code:\n\n```rust\n{code}\n```\n\nJudge this rule only; ignore "
              f"anything else the code does. Answer the question.{extra}\n\nReply with JSON only: "
              '{"evidence": "<the lines that decide it, and why>", "violates": true|false'
              + (', "kept": true|false' if keep else "") + "}. Write the evidence first and set the "
              "booleans to what it concludes.")
    out = claude(prompt, str(JUDGMENT), GRADER_SYSTEM, replace_system=True, model=model, dry_run=dry_run)
    if dry_run:
        return {"violates": None, "kept": None, "evidence": "", "usage": {}}
    m = re.search(r"\{.*\}", out.get("result", ""), re.S)
    verdict = json.loads(m.group(0)) if m else {}
    if not isinstance(verdict.get("violates"), bool) or (keep and not isinstance(verdict.get("kept"), bool)):
        raise RuntimeError(f"{rule}: grader returned no verdict: {out.get('result', '')[:300]}")
    return {**verdict, "usage": out.get("usage", {})}


def fix(code, arm, model, dry_run):
    system = None
    if arm == "skill":
        system = ("The rust-style-guide skill is loaded for this task.\n\n"
                  + (ASSETS.parent / "SKILL.md").read_text())
    prompt = ("This is `src/module.rs` from a library crate of ours (thiserror, serde, serde_json and tokio are "
              "dependencies). Fix what needs fixing in it. Reply with the complete revised file in one ```rust "
              f"block and nothing else.\n\n```rust\n{code}\n```")
    out = claude(prompt, str(JUDGMENT), system, model=model, dry_run=dry_run)
    if dry_run:
        return code, {}
    m = re.search(r"```rust\n(.*?)```", out.get("result", ""), re.S)
    if not m:
        raise RuntimeError(f"fix run returned no rust block: {out.get('result', '')[:300]}")
    return m.group(1), out.get("usage", {})


def parallel(fn, items, jobs):
    # The first call runs alone: it writes the prompt cache (SKILL.md, in a skill run) that the rest
    # then read, instead of `jobs` calls each paying to write it.
    with ThreadPoolExecutor(jobs) as pool:
        first = pool.submit(fn, items[0]) if items else None
        if first:
            first.exception()  # wait
        futures = ([first] if first else []) + [pool.submit(fn, item) for item in items[1:]]
    results = []
    for item, future in zip(items, futures):
        try:
            results.append(future.result())
        except Exception as exc:  # one failed call shouldn't throw away the batch
            print(f"skipped {item}: {exc}", file=sys.stderr)
            results.append(None)
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--judgment", action="store_true")
    mode.add_argument("--fix", action="store_true")
    ap.add_argument("--rules", help="comma-separated rule directories (default: all)")
    ap.add_argument("--only", help="comma-separated rule/file samples, e.g. overflow/bad.rs (default: all)")
    ap.add_argument("--arms", default="skill,none", help="--fix arms; `none` alone screens what the bare model already fixes")
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("-j", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    rules = a.rules.split(",") if a.rules else sorted(d.name for d in JUDGMENT.iterdir() if d.is_dir() and not d.name.startswith("."))
    items = list(samples(rules))
    if a.only:
        wanted = set(a.only.split(","))
        items = [i for i in items if f"{i[0]}/{i[2].name}" in wanted]
        if missing := wanted - {f"{r}/{f.name}" for r, _, f in items}:
            sys.exit(f"no such sample: {', '.join(sorted(missing))}")
    problems = [] if a.only else [f"{r}: no {k} sample" for r in rules for k in ("bad", "good")
                if not any(rule == r and kind == k for rule, kind, _ in items)]
    problems += [f"{r}: no rule.md" for r in rules if not (JUDGMENT / r / "rule.md").exists()]
    if problems:
        sys.exit("FAIL\n" + "\n".join(f"- {p}" for p in problems))

    if not (a.judgment or a.fix):
        found, stray = lint_check({module(r, f): code_and_keep(f)[0] for r, _, f in items})
        bad = [f"{name}: {status} {diags}" for name, (status, diags) in found.items() if status != "clean"] + stray
        if bad:
            print("FAIL\n" + "\n".join(f"- {b}" for b in bad))
            return 1
        print(f"ok ({len(items)} judgment samples in {len(rules)} rules compile and pass the lint set)")
        return 0

    out_dir = REPO / ".bench" / f"rsg-rules-{time.strftime('%Y%m%d-%H%M%S')}"
    if a.judgment:
        calls = len(items)
        print(f"{calls} grading calls with {a.model}, about {calls * EST['grade'] / 1e3:.0f}k fresh input tokens")

        def judge(item):
            rule, kind, f = item
            code, keep = code_and_keep(f)
            return grade(rule, code, None, a.model, a.dry_run)

        verdicts = parallel(judge, items, a.j)
        rows = []
        for (rule, kind, f), v in zip(items, verdicts):
            want = kind == "bad"
            ok = v is not None and v["violates"] == want
            rows.append({"rule": rule, "sample": f.name, "kind": kind, "ok": ok, "verdict": v})
        summary = [f"{r['rule']}/{r['sample']}: expected {'flag' if r['kind'] == 'bad' else 'clean'}, got "
                   f"{'nothing' if r['verdict'] is None else 'flag' if r['verdict']['violates'] else 'clean'}"
                   for r in rows if not r["ok"]]
        score = f"{sum(r['ok'] for r in rows)}/{len(rows)} samples graded as expected"
    else:
        targets = [i for i in items if i[1] in ("bad", "allowed")]
        arms = a.arms.split(",")
        runs = [(arm, *t) for arm in arms for t in targets]
        est = sum(EST[f"fix-{arm}"] + EST["grade"] for arm, *_ in runs) + EST["skill-cache-write"] * ("skill" in arms)
        print(f"{len(runs)} fix runs + {len(runs)} grading calls with {a.model}, about {est / 1e3:.0f}k fresh input tokens (plus cached reads)")

        def fixed(run):
            arm, rule, kind, f = run
            code, keep = code_and_keep(f)
            revised, usage = fix(code, arm, a.model, a.dry_run)
            return {"revised": revised, "usage": usage, "verdict": grade(rule, revised, keep, a.model, a.dry_run)}

        outcomes = parallel(fixed, runs, a.j)
        names = {f"{arm}_{module(rule, f)}": o["revised"] for (arm, rule, _, f), o in zip(runs, outcomes) if o}
        lints, stray = ({}, []) if a.dry_run else lint_check(names)
        rows = []
        for (arm, rule, kind, f), o in zip(runs, outcomes):
            v = o and o["verdict"]
            rule_ok = bool(v) and v["violates"] is False and (keep_of(f) is None or v.get("kept") is True)
            status, diags = lints.get(f"{arm}_{module(rule, f)}", ("unknown", []))
            # The guide includes its lint set: a fix that doesn't compile or trips a lint isn't done.
            rows.append({"arm": arm, "rule": rule, "sample": f.name, "kind": kind,
                         "ok": rule_ok and status == "clean", "rule_ok": rule_ok, "build": status,
                         "lints": diags, **(o or {})})
        summary = []
        for arm in arms:
            mine = [r for r in rows if r["arm"] == arm]
            for kind in ("bad", "allowed"):
                part = [r for r in mine if r["kind"] == kind]
                label = "fixed" if kind == "bad" else "left alone"
                builds = {b: sum(r["build"] == b for r in part) for b in ("clean", "lints", "broken", "unknown")}
                summary.append(f"{arm:5} {kind:7} {label} and lint-clean: {sum(r['ok'] for r in part)}/{len(part)}"
                               f"  (rule alone {sum(r['rule_ok'] for r in part)}/{len(part)}; build {builds})  "
                               "misses: " + (", ".join(f"{r['rule']}/{r['sample']} ({r['build']})"
                                                       for r in part if not r["ok"]) or "none"))
        summary += [f"diagnostic outside the fix files: {s}" for s in stray]
        score = f"{len(runs)} runs"
    if a.dry_run:
        print("dry run: no calls made")
        return 0
    out_dir.mkdir(parents=True)
    (out_dir / "results.json").write_text(json.dumps(rows, indent=1))
    print(score + "\n" + "\n".join(summary) + f"\n{out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

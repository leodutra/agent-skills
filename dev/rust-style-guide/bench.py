#!/usr/bin/env python3
"""Cheap blind A/B of rust-style-guide: the working tree's skill against a git ref, through lean
`claude -p` sessions (the flags dev/gauntlet-loop/eval/run.sh uses: no settings, no MCP, only the
tools a run needs). No Claude session stays open while it runs, so nothing re-reads a long context.

  python3 dev/rust-style-guide/bench.py [--ref HEAD] [--cases a,b | --all] [--new-only] [--model sonnet] [-j 4] [--dry-run]

A review case is one tool-less call: SKILL.md as the system prompt, the input files inline, the
reply saved as review.md. A code case gets Read/Write/Edit in its own directory and Bash approved
for `cargo` and `tail` only (other commands are refused); cargo still runs added crates' build scripts. Graders 01/02 of code cases are grade_cargo.py; every other grader is one tool-less call per
run that sees only that run's output, never its arm, under a one-line system prompt instead of the
coding-agent one. --ref must name a commit whose skill differs from the working tree's; the script
refuses to compare a skill with itself. --new-only runs the same cases and graders for the current
skill, without a baseline arm; use the default A/B when comparing versions. Workspace:
.bench/rsg-<time>/ (git-excluded); --regrade re-grades one without new runs. It spends your
claude.ai usage: the default four cases make 8 runs and 8 grading calls, about 400k input tokens
with Sonnet (2026-11-12); --all runs every case."""
import argparse, json, os, random, re, shutil, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
EVALS = os.path.join(HERE, "evals")
# The cases that told the versions apart on 2026-11-12, plus one code case and one control.
DEFAULT = ["review-inventory-module", "review-published-crate", "customer-lookup", "review-payments-module"]
strip = lambda s: re.sub(r"(?s)\A---\n.*?\n---\n\n", "", s).strip()

ap = argparse.ArgumentParser()
ap.add_argument("--ref", default="HEAD")
selection = ap.add_mutually_exclusive_group()
selection.add_argument("--cases")
selection.add_argument("--all", action="store_true", help="run every case, not the default four")
ap.add_argument("--model", default="sonnet")
ap.add_argument("-j", type=int, default=4)
ap.add_argument("--dry-run", action="store_true")
ap.add_argument("--new-only", action="store_true", help="grade the current skill without a baseline arm")
ap.add_argument("--regrade", metavar="WORKSPACE", help="grade an earlier workspace again; no new runs")
a = ap.parse_args()
if a.cases:
    cases = a.cases.split(",")
elif a.all:
    cases = sorted(c for c in os.listdir(EVALS) if os.path.exists(f"{EVALS}/{c}/prompt.md"))
else:
    cases = DEFAULT

if a.regrade:
    W = os.path.abspath(a.regrade)
else:
    bench_root = os.path.join(REPO, ".bench")
    os.makedirs(bench_root, exist_ok=True)
    W = tempfile.mkdtemp(prefix="rsg-" + time.strftime("%Y%m%d-%H%M%S") + "-", dir=bench_root)
skills = {"new": f"{W}/s1/rust-style-guide", "old": f"{W}/s2/rust-style-guide"}
is_review = lambda c: os.path.exists(f"{EVALS}/{c}/place-files.sh")
if a.regrade:
    mapping = json.load(open(f"{W}/mapping.json"))
else:
    shutil.copytree(f"{REPO}/skills/rust-style-guide", skills["new"], ignore=shutil.ignore_patterns(".*"))
    if not a.new_only:
        os.makedirs(f"{W}/s2")
        tar = subprocess.run(["git", "-C", REPO, "archive", a.ref, "skills/rust-style-guide"], capture_output=True, check=True).stdout
        subprocess.run(["tar", "-x", "-C", f"{W}/s2", "--strip-components=1"], input=tar, check=True)
        if subprocess.run(["diff", "-rq", skills["new"], skills["old"]], capture_output=True).returncode == 0:
            shutil.rmtree(W)
            sys.exit(f"the working tree's skill is identical to {a.ref}'s: nothing to compare (pass --ref <older commit>)")
    plan = [(c, arm) for c in cases for arm in (("new",) if a.new_only else ("new", "old"))]
    ids = [f"r{n:02d}" for n in range(1, len(plan) + 1)]
    random.shuffle(ids)
    mapping = {rid: {"case": c, "arm": arm} for rid, (c, arm) in zip(ids, plan)}
    json.dump(mapping, open(f"{W}/mapping.json", "w"), indent=1)


def claude(prompt, cwd, system=None, tools="", extra=(), replace_system=False):
    cmd = ["claude", "-p", prompt, "--tools", tools, "--setting-sources", "", "--strict-mcp-config",
           "--no-session-persistence", "--model", a.model, "--output-format", "json", *extra]
    if system: cmd += ["--system-prompt" if replace_system else "--append-system-prompt", system]
    if a.dry_run: return {"result": "", "usage": {}, "dry_run": " ".join(cmd[:2] + cmd[3:])[:300]}
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=1800)
    try:
        out = json.loads(p.stdout)
    except ValueError as exc:
        raise RuntimeError(f"claude returned non-JSON (exit {p.returncode}): {(p.stdout + p.stderr)[-1000:]}") from exc
    if p.returncode or out.get("is_error") or out.get("terminal_reason") == "api_error":
        reason = out.get("api_error") or out.get("error") or out.get("result") or p.stderr
        raise RuntimeError(f"claude failed (exit {p.returncode}): {str(reason)[:500]}")
    return out


def inputs(case):
    root = f"{EVALS}/{case}/files"
    return "\n\n".join(f"`{os.path.relpath(os.path.join(d, f), root)}`:\n```rust\n{open(os.path.join(d, f)).read()}```"
                       for d, _, fs in sorted(os.walk(root)) for f in sorted(fs))


def run(rid):
    case, arm = mapping[rid]["case"], mapping[rid]["arm"]
    d, skill = f"{W}/runs/{rid}", skills[arm]
    os.makedirs(d)
    system = ("The rust-style-guide skill is loaded for this task"
              + ("." if is_review(case) else f"; its files are in {skill}.") + "\n\n" + open(f"{skill}/SKILL.md").read())
    task = strip(open(f"{EVALS}/{case}/prompt.md").read())
    if is_review(case):
        subprocess.run(["bash", f"{EVALS}/{case}/place-files.sh"], cwd=d, check=True)
        out = claude(f"{task}\n\nThe input files:\n\n{inputs(case)}\n\nReply with the full text of review.md and "
                     "nothing else.", d, system)
        if not a.dry_run and not out.get("result", "").strip():
            raise RuntimeError(f"{case}: review call returned no text")
        open(f"{d}/review.md", "w").write(out.get("result", ""))
    else:
        # Bash is pre-approved for cargo (and read-only tail) only; any other command is refused, not prompted.
        # cargo still runs build scripts of the crates a run adds, as any cargo build does.
        out = claude(f"{task}\n\nWork in the current directory: create the cargo project in it (`cargo init`). "
                     "Only `cargo` commands (and `tail`) are allowed in Bash; write files with Write and Edit. "
                     "Keep command output short (--quiet). End with at most three lines on what you ran.",
                     d, system, "Read,Write,Edit,Bash",
                     ["--allowedTools", "Read,Write,Edit,Bash(cargo:*),Bash(tail:*)", "--add-dir", skill])
    json.dump(out, open(f"{d}/claude.json", "w"))
    return rid


def grade(rid):
    case, d = mapping[rid]["case"], f"{W}/runs/{rid}"
    gs = sorted(os.listdir(f"{EVALS}/{case}/graders"))
    if not is_review(case):
        if not a.dry_run:
            c = subprocess.run([sys.executable, "-I", f"{HERE}/grade_cargo.py", d], capture_output=True, text=True)
            open(f"{d}/cargo.json", "w").write(c.stdout)
        gs = [g for g in gs if not g.startswith(("01-", "02-"))]
        hidden = lambda r: any(p == "target" or p.startswith(".") for p in os.path.relpath(r, d).split(os.sep) if p != ".")
        files = [os.path.join(r, f) for r, _, fs in os.walk(d) if not hidden(r) for f in fs if f.endswith((".rs", ".toml"))]
        output = "\n\n".join(f"`{os.path.relpath(f, d)}`:\n```\n{open(f).read()}```" for f in sorted(files))
    else:
        output = f"The input files:\n\n{inputs(case)}\n\nreview.md:\n\n{open(f'{d}/review.md').read()}"
    asserts = [strip(open(f"{EVALS}/{case}/graders/{g}").read()) for g in gs]
    prompt = ("Grade one assistant output against assertions. PASS needs clear evidence; when unsure, FAIL. An "
              "assertion that says review.md \"does not\" call something a defect passes only if review.md never "
              "calls it a defect or asks to change it, not even as a nit or a \"consider\".\n\nThe task:\n\n"
              + strip(open(f"{EVALS}/{case}/prompt.md").read()) + "\n\nThe output:\n\n" + output + "\n\nAssertions:\n"
              + "\n".join(f"{i + 1}. {s}" for i, s in enumerate(asserts))
              + '\n\nReply with JSON only: {"expectations": [{"text": "<assertion>", "evidence": "<short quote '
                'and your reasoning>", "passed": true|false}, ...]}, one entry per assertion, in order. Write the '
                'evidence first and set "passed" to what it concludes.')
    # A grader needs no coding-agent prompt: replacing it keeps the call to the grading text alone.
    for _ in range(2):  # one retry: a call now and then comes back empty
        out = claude(prompt, d, "You grade an assistant's output against assertions and reply with JSON only.",
                     replace_system=True)
        m = re.search(r"\{.*\}", out.get("result", ""), re.S)
        if m: break
    if not m and not a.dry_run:
        raise RuntimeError(f"{case}: grader returned no JSON: {str(out.get('result', ''))[:500]}")
    verdict = json.loads(m.group(0)) if m else {"expectations": []}
    if not a.dry_run and (len(verdict.get("expectations", [])) != len(gs)
                          or any(not isinstance(e.get("passed"), bool) for e in verdict["expectations"])):
        raise RuntimeError(f"{case}: grader returned incomplete assertions")
    json.dump({**verdict, "usage": out.get("usage", {})}, open(f"{d}/grading.json", "w"), indent=1)
    return rid


if not a.regrade:
    with ThreadPoolExecutor(a.j) as ex: list(ex.map(run, sorted(mapping)))
to_grade = sorted(r for r in mapping if not a.cases or mapping[r]["case"] in a.cases.split(","))
with ThreadPoolExecutor(a.j) as ex: list(ex.map(grade, to_grade))

# Unblind: score per case and arm, and the tokens every call reported.
score, tokens = {}, 0
for rid, m in sorted(mapping.items()):
    d = f"{W}/runs/{rid}"; p = n = 0; fails = []
    g = json.load(open(f"{d}/grading.json"))
    if os.path.exists(f"{d}/cargo.json") and os.path.getsize(f"{d}/cargo.json"):
        c = json.load(open(f"{d}/cargo.json"))
        for k in ("test_passed", "clippy_current_lints"):
            n += 1; p += bool(c.get(k)); fails += [] if c.get(k) else [k]
    for e in g.get("expectations", []):
        n += 1; p += bool(e.get("passed")); fails += [] if e.get("passed") else [e.get("text", "")[:80]]
    for f in ("claude.json",):
        u = json.load(open(f"{d}/{f}")).get("usage", {})
        tokens += sum(u.get(k, 0) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
    tokens += sum(g.get("usage", {}).get(k, 0) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
    score.setdefault(m["case"], {})[m["arm"]] = (p, n, fails)
has_old = any("old" in s for s in score.values())
for c, s in score.items():
    line = f"{c:26} new {s['new'][0]}/{s['new'][1]}"
    if "old" in s:
        line += f"   {a.ref} {s['old'][0]}/{s['old'][1]}"
    print(line)
    for arm in s:
        for f in s[arm][2]: print(f"    {arm} FAIL: {f}")
summary = f"total new {sum(s['new'][0] for s in score.values())}/{sum(s['new'][1] for s in score.values())}"
if has_old:
    summary += f"   {a.ref} {sum(s['old'][0] for s in score.values())}/{sum(s['old'][1] for s in score.values())}"
print(f"{summary}   input tokens {tokens:,}   workspace {W}")

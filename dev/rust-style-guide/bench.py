#!/usr/bin/env python3
"""Cheap blind A/B of rust-style-guide: the working tree's skill against a git ref, through lean
`claude -p` sessions (the flags dev/gauntlet-loop/eval/run.sh uses: no settings, no MCP, only the
tools a run needs). No Claude session stays open while it runs, so nothing re-reads a long context.

  python3 dev/rust-style-guide/bench.py [--ref HEAD] [--cases a,b | --all] [--new-only] [--no-skill] [--model sonnet] [-j 4] [--dry-run]

A review case is one tool-less call: SKILL.md as the system prompt, the input files inline, the
reply saved as review.md. A code case gets Read/Write/Edit in its own directory and Bash approved
for `cargo` and `tail` only (other commands are refused); cargo still runs added crates' build scripts. Graders 01/02 of code cases are grade_cargo.py; every other grader is one tool-less call per
run that sees only that run's output, never its arm, under a one-line system prompt instead of the
coding-agent one. --ref must name a commit whose skill differs from the working tree's; the script
refuses to compare a skill with itself. --new-only runs the same cases and graders for the current
skill, without a baseline arm; use the default A/B when comparing versions. A call that fails is
retried once, then skipped with its error printed; --resume WORKSPACE finishes only the runs and
gradings still missing. --samples N runs each case and arm N times and prints each sample's
total per arm, so a small gap can be read against the spread. A grading call the safety filter
refuses is retried once with --grade-fallback (default opus), recorded as graded_by.

Validity. Each grader's front matter says its kind: `correctness` (a defect any competent Rust
reviewer would call a bug: a panic, a wrong result, lost data, a leaked secret, an invariant
input can break) or `convention` (this skill's own rule, which another guide may not share). The
table reports the two apart; only the correctness total can show better code, the convention
total shows the skill is followed. Graders are frozen per workspace: --resume and --regrade refuse
a case whose graders changed since the run, unless --grader-change "<reason>" is given, which
regrades that case in every arm and logs the change in grader-changes.md. --report WORKSPACE
prints a workspace's table with no calls. --validate grades each case's reference/ (a correct
answer: every assertion must pass) and mainstream/ (the common answer: it must fail the graders
named in mainstream/expected-fails), so a grader is trusted only once it tells them apart. A code case
may have hidden/tests/hidden.rs: behavioral tests against the API its prompt pins, never shown to a
run, run by grade_cargo.py; each counts as one correctness assertion (`hidden` in expected-fails means
at least one fails). A case with no LLM graders makes no grading call.

--no-skill adds an arm
with no skill loaded (same task, no system prompt added), so a case shows what the skill itself buys. Workspace:
.bench/rsg-<time>/ (git-excluded); --regrade re-grades one without new runs. It spends your
claude.ai usage: one arm of the default two cases is about 0.3M input tokens with Sonnet
(a code run ~150k, a review run ~18k, a grading call ~7k; 2026-11-15)."""
import argparse, hashlib, json, os, random, re, shutil, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor
import claude_cli

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
EVALS = os.path.join(HERE, "evals")
# The cases that separate the skill from no skill (2026-11-15, 3 samples); the unproven ones were dropped.
DEFAULT = ["rate-limit-config", "ticket-reassign"]
strip = lambda s: re.sub(r"(?s)\A---\n.*?\n---\n\n", "", s).strip()

ap = argparse.ArgumentParser()
ap.add_argument("--ref", default="HEAD")
selection = ap.add_mutually_exclusive_group()
selection.add_argument("--cases")
selection.add_argument("--all", action="store_true", help="run every case")
ap.add_argument("--model", default="sonnet")
ap.add_argument("--samples", type=int, default=1, help="runs per case and arm")
ap.add_argument("--grade-fallback", default="opus", help="grading model when the safety filter refuses a grading call")
ap.add_argument("-j", type=int, default=4)
ap.add_argument("--dry-run", action="store_true")
ap.add_argument("--new-only", action="store_true", help="grade the current skill without a baseline arm")
ap.add_argument("--no-skill", action="store_true", help="add an arm with no skill loaded")
ap.add_argument("--regrade", metavar="WORKSPACE", help="grade an earlier workspace again; no new runs")
ap.add_argument("--resume", metavar="WORKSPACE", help="finish the missing runs and gradings of a workspace")
ap.add_argument("--report", metavar="WORKSPACE", help="print a workspace's table; no calls")
ap.add_argument("--grader-change", metavar="REASON", help="accept changed graders: regrade those cases in every arm, log why")
ap.add_argument("--validate", action="store_true", help="grade each case's reference/ and mainstream/ answers")
a = ap.parse_args()
existing = a.regrade or a.resume or a.report
if a.dry_run and existing:
    # A dry run writes placeholder results; in an existing workspace they would overwrite the real ones.
    sys.exit("--dry-run only makes a new workspace; it can't be combined with --regrade or --resume")
if a.cases:
    cases = a.cases.split(",")
elif a.all or a.validate:
    cases = sorted(c for c in os.listdir(EVALS) if os.path.exists(f"{EVALS}/{c}/prompt.md"))
else:
    cases = DEFAULT

if a.validate:
    cases = [c for c in cases if os.path.isdir(f"{EVALS}/{c}/reference")]
if existing:
    W = os.path.abspath(existing)
else:
    bench_root = os.path.join(REPO, ".bench")
    os.makedirs(bench_root, exist_ok=True)
    W = tempfile.mkdtemp(prefix="rsg-" + time.strftime("%Y%m%d-%H%M%S") + "-", dir=bench_root)
skills = {"new": f"{W}/s1/rust-style-guide", "old": f"{W}/s2/rust-style-guide"}
is_review = lambda c: os.path.exists(f"{EVALS}/{c}/place-files.sh")


def graders(case):
    """(file, kind, assertion) per LLM grader of a case, in order; a code case's 01/02 are grade_cargo's."""
    out = []
    for g in sorted(g for g in os.listdir(f"{EVALS}/{case}/graders") if not g.startswith(".")):
        if not is_review(case) and g.startswith(("01-", "02-")): continue
        text = open(f"{EVALS}/{case}/graders/{g}").read()
        kind = re.search(r"(?m)^kind: (\w+)$", text)
        out.append((g, kind.group(1) if kind else "untagged", strip(text)))
    return out


fingerprint = lambda case: hashlib.sha256(json.dumps([(g, t) for g, _, t in graders(case)]).encode()).hexdigest()[:16]
if a.validate:
    W = tempfile.mkdtemp(prefix="rsg-validate-" + time.strftime("%Y%m%d-%H%M%S") + "-", dir=os.path.join(REPO, ".bench"))
    mapping = {}
    for c in cases:
        for arm in ("reference", "mainstream"):
            src = f"{EVALS}/{c}/{arm}"
            if not os.path.isdir(src): continue
            rid = f"r{len(mapping) + 1:02d}"
            shutil.copytree(src, f"{W}/runs/{rid}", ignore=shutil.ignore_patterns("expected-fails", "target"))
            json.dump({}, open(f"{W}/runs/{rid}/claude.json", "w"))
            mapping[rid] = {"case": c, "arm": arm, "sample": 0}
    json.dump(mapping, open(f"{W}/mapping.json", "w"), indent=1)
elif existing:
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
    arms = (("new",) if a.new_only else ("new", "old")) + (("none",) if a.no_skill else ())
    plan = [(c, arm, k) for c in cases for arm in arms for k in range(a.samples)]
    ids = [f"r{n:02d}" for n in range(1, len(plan) + 1)]
    random.shuffle(ids)
    mapping = {rid: {"case": c, "arm": arm, "sample": k} for rid, (c, arm, k) in zip(ids, plan)}
    json.dump(mapping, open(f"{W}/mapping.json", "w"), indent=1)
if not existing:
    json.dump({c: fingerprint(c) for c in {m["case"] for m in mapping.values()}}, open(f"{W}/graders.json", "w"), indent=1)
    changed = []
else:
    # Graders are frozen per workspace: a verdict only counts against the graders it was given.
    frozen = json.load(open(f"{W}/graders.json")) if os.path.exists(f"{W}/graders.json") else {}
    if not frozen:
        print(f"note: {W} predates frozen graders" + ("" if a.report else "; freezing the current ones now"), file=sys.stderr)
    changed = sorted(c for c in {m["case"] for m in mapping.values()} if frozen and frozen.get(c) != fingerprint(c))
    if changed and a.report:
        print(f"warning: graders changed since grading for {', '.join(changed)}; their verdicts are stale", file=sys.stderr)
    elif changed and not a.grader_change:
        sys.exit(f"graders changed since this workspace was graded: {', '.join(changed)}. Pass --grader-change "
                 '"<reason>" to regrade those cases in every arm and log the change.')
    elif changed:
        with open(f"{HERE}/grader-changes.md", "a") as log:
            log.write(f"- {time.strftime('%Y-%m-%d')} {os.path.basename(W)}: {', '.join(changed)} — {a.grader_change}\n")
    if not a.report:
        json.dump({c: fingerprint(c) for c in {m["case"] for m in mapping.values()}}, open(f"{W}/graders.json", "w"), indent=1)


def claude(prompt, cwd, system=None, tools="", extra=(), replace_system=False, model=None):
    return claude_cli.claude(prompt, cwd, system, tools, extra, replace_system, model or a.model, a.dry_run)


def inputs(case):
    root = f"{EVALS}/{case}/files"
    return "\n\n".join(f"`{os.path.relpath(os.path.join(d, f), root)}`:\n```rust\n{open(os.path.join(d, f)).read()}```"
                       for d, _, fs in sorted(os.walk(root)) for f in sorted(fs))


def run(rid):
    case, arm = mapping[rid]["case"], mapping[rid]["arm"]
    d, skill = f"{W}/runs/{rid}", skills.get(arm)
    os.makedirs(d, exist_ok=True)
    system = skill and ("The rust-style-guide skill is loaded for this task"
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
                     ["--allowedTools", "Read,Write,Edit,Bash(cargo:*),Bash(tail:*)"] + (["--add-dir", skill] if skill else []))
    json.dump(out, open(f"{d}/claude.json", "w"))
    return rid


def grade(rid):
    case, d = mapping[rid]["case"], f"{W}/runs/{rid}"
    gs = graders(case)
    if not is_review(case):
        if not a.dry_run:
            hidden = [f"{EVALS}/{case}/hidden"] if os.path.isdir(f"{EVALS}/{case}/hidden") else []
            c = subprocess.run([sys.executable, "-I", f"{HERE}/grade_cargo.py", d, *hidden], capture_output=True, text=True)
            open(f"{d}/cargo.json", "w").write(c.stdout)
        hidden = lambda r: any(p == "target" or p.startswith(".") for p in os.path.relpath(r, d).split(os.sep) if p != ".")
        files = [os.path.join(r, f) for r, _, fs in os.walk(d) if not hidden(r) for f in fs if f.endswith((".rs", ".toml"))]
        output = "\n\n".join(f"`{os.path.relpath(f, d)}`:\n```\n{open(f).read()}```" for f in sorted(files))
    else:
        output = f"The input files:\n\n{inputs(case)}\n\nreview.md:\n\n{open(f'{d}/review.md').read()}"
    asserts = [t for _, _, t in gs]
    if not asserts:  # hidden tests and cargo are the whole grade
        json.dump({"expectations": [], "kinds": [], "graded_by": "cargo", "usage": {}}, open(f"{d}/grading.json", "w"))
        return rid
    prompt = ("Grade one assistant output against assertions. PASS needs clear evidence; when unsure, FAIL. An "
              "assertion that says review.md \"does not\" call something a defect passes only if review.md never "
              "calls it a defect or asks to change it, not even as a nit or a \"consider\".\n\nThe task:\n\n"
              + strip(open(f"{EVALS}/{case}/prompt.md").read()) + "\n\nThe output:\n\n" + output + "\n\nAssertions:\n"
              + "\n".join(f"{i + 1}. {s}" for i, s in enumerate(asserts))
              + '\n\nReply with JSON only: {"expectations": [{"text": "<assertion>", "evidence": "<short quote '
                'and your reasoning>", "passed": true|false}, ...]}, one entry per assertion, in order. Write the '
                'evidence first and set "passed" to what it concludes.')
    # A grader needs no coding-agent prompt: replacing it keeps the call to the grading text alone.
    graded_by = a.model
    for _ in range(2):  # one retry: a call now and then comes back empty
        try:
            out = claude(prompt, d, "You grade an assistant's output against assertions and reply with JSON only.",
                         replace_system=True, model=graded_by)
        except RuntimeError as exc:
            # The safety filter sometimes refuses a harmless grading call, and refuses it again on retry
            # with the same model; another model grades it instead, and the file says which.
            if "safeguards flagged" not in str(exc) or graded_by == a.grade_fallback: raise
            graded_by = a.grade_fallback
            continue
        m = re.search(r"\{.*\}", out.get("result", ""), re.S)
        if m: break
    if not m and not a.dry_run:
        raise RuntimeError(f"{case}: grader returned no JSON: {str(out.get('result', ''))[:500]}")
    verdict = json.loads(m.group(0)) if m else {"expectations": []}
    if not a.dry_run and (len(verdict.get("expectations", [])) != len(gs)
                          or any(not isinstance(e.get("passed"), bool) for e in verdict["expectations"])):
        raise RuntimeError(f"{case}: grader returned incomplete assertions")
    json.dump({**verdict, "kinds": [k for _, k, _ in gs], "graded_by": graded_by, "usage": out.get("usage", {})},
              open(f"{d}/grading.json", "w"), indent=1)
    return rid


def retried(step):
    # A call now and then fails for no reason of its own (an empty reply, a false safety flag): retry once,
    # then report and skip it, so one bad call doesn't throw away the rest of the batch.
    def attempt(rid):
        for n in (1, 2):
            try:
                return step(rid)
            except Exception as exc:
                if n == 2 or "usage_limit_reached" in str(exc):  # retrying a spent limit only spends nothing twice
                    print(f"SKIPPED {step.__name__} {rid} {mapping[rid]}: {str(exc)[:300]}", file=sys.stderr)
    return attempt


done = lambda rid, f: os.path.exists(f"{W}/runs/{rid}/{f}")
if not (a.regrade or a.report or a.validate):
    to_run = sorted(r for r in mapping if not (a.resume and done(r, "claude.json")))
    with ThreadPoolExecutor(a.j) as ex: list(ex.map(retried(run), to_run))
if not a.report:
    to_grade = sorted(r for r in mapping if (a.validate or not a.cases or mapping[r]["case"] in a.cases.split(","))
                      and done(r, "claude.json")
                      and not (a.resume and done(r, "grading.json") and mapping[r]["case"] not in changed))
    with ThreadPoolExecutor(a.j) as ex: list(ex.map(retried(grade), to_grade))

if a.validate:
    # A grader is trusted once it tells a correct answer from the common one.
    bad = 0
    for rid, m in sorted(mapping.items(), key=lambda kv: (kv[1]["case"], kv[1]["arm"])):
        d = f"{W}/runs/{rid}"
        if not done(rid, "grading.json"):
            print(f"{m['case']} {m['arm']}: not graded"); bad += 1; continue
        verdicts = {g: e["passed"] for (g, _, _), e in zip(graders(m["case"]), json.load(open(f"{d}/grading.json"))["expectations"])}
        if done(rid, "cargo.json") and os.path.getsize(f"{d}/cargo.json"):
            c = json.load(open(f"{d}/cargo.json"))
            for g in os.listdir(f"{EVALS}/{m['case']}/graders"):
                if g.startswith("01-"): verdicts[g] = bool(c.get("test_passed"))
                if g.startswith("02-"): verdicts[g] = bool(c.get("clippy_current_lints"))
            if "hidden_total" in c: verdicts["hidden"] = c["hidden_passed"] == c["hidden_total"]
        expect_fail = set()
        if m["arm"] == "mainstream":
            expect_fail = set(open(f"{EVALS}/{m['case']}/mainstream/expected-fails").read().split())
        for g, passed in sorted(verdicts.items()):
            want = g.split("-")[0] not in {x.split("-")[0] for x in expect_fail}
            if passed != want:
                bad += 1
                print(f"MISGRADED {m['case']} {m['arm']} {g}: expected {'pass' if want else 'fail'}, got {'pass' if passed else 'fail'}")
    print(f"validate: {len(mapping)} answers, {bad} misgraded   workspace {W}")
    sys.exit(1 if bad else 0)

# Unblind: score per case and arm, and the tokens every call reported.
score, tokens, per_sample, by_kind = {}, 0, {}, {}
missing = sorted(r for r in mapping if not done(r, "grading.json"))
for rid in missing:
    print(f"MISSING {rid} {mapping[rid]['case']} {mapping[rid]['arm']}: not scored (rerun with --resume {W})")
for rid, m in sorted(mapping.items()):
    if rid in missing: continue
    d = f"{W}/runs/{rid}"; p = n = 0; fails = []
    g = json.load(open(f"{d}/grading.json"))
    # Older gradings carry no kinds: take them from the current graders by position.
    kinds = g.get("kinds") or [k for _, k, _ in graders(m["case"])]
    tally = by_kind.setdefault(m["arm"], {})
    if os.path.exists(f"{d}/cargo.json") and os.path.getsize(f"{d}/cargo.json"):
        c = json.load(open(f"{d}/cargo.json"))
        for k, kind in (("test_passed", "correctness"), ("clippy_current_lints", "convention")):
            n += 1; p += bool(c.get(k)); fails += [] if c.get(k) else [k]
            t = tally.setdefault(kind, [0, 0]); t[0] += bool(c.get(k)); t[1] += 1
        if "hidden_total" in c:
            hp, hn = c["hidden_passed"], c["hidden_total"]
            n += hn; p += hp; fails += [] if hp == hn else [f"hidden tests {hp}/{hn}"]
            for kind in ("correctness", "hidden"):
                t = tally.setdefault(kind, [0, 0]); t[0] += hp; t[1] += hn
    for i, e in enumerate(g.get("expectations", [])):
        n += 1; p += bool(e.get("passed")); fails += [] if e.get("passed") else [e.get("text", "")[:80]]
        t = tally.setdefault(kinds[i] if i < len(kinds) else "untagged", [0, 0]); t[0] += bool(e.get("passed")); t[1] += 1
    for f in ("claude.json",):
        u = json.load(open(f"{d}/{f}")).get("usage", {})
        tokens += sum(u.get(k, 0) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
    tokens += sum(g.get("usage", {}).get(k, 0) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
    sp, sn, sf = score.setdefault(m["case"], {}).get(m["arm"], (0, 0, []))
    score[m["case"]][m["arm"]] = (sp + p, sn + n, sf + fails)
    per_sample.setdefault(m["arm"], {}).setdefault(m.get("sample", 0), [0, 0])
    per_sample[m["arm"]][m.get("sample", 0)][0] += p; per_sample[m["arm"]][m.get("sample", 0)][1] += n
label = {"new": "new", "old": a.ref, "none": "no-skill"}
present = [arm for arm in label if any(arm in s for s in score.values())]
for c, s in score.items():
    print(f"{c:28}" + "   ".join(f"{label[arm]} {s[arm][0]}/{s[arm][1]}" for arm in present if arm in s))
    for arm in s:
        for f in s[arm][2]: print(f"    {label[arm]} FAIL: {f}")
summary = "total " + "   ".join(f"{label[arm]} {sum(s[arm][0] for s in score.values() if arm in s)}/"
                                f"{sum(s[arm][1] for s in score.values() if arm in s)}" for arm in present)
for kind in sorted({k for t in by_kind.values() for k in t}):
    print(f"{kind:12}" + "   ".join(f"{label[arm]} {by_kind[arm][kind][0]}/{by_kind[arm][kind][1]}"
                                   for arm in present if kind in by_kind.get(arm, {})))
if any(len(v) > 1 for v in per_sample.values()):
    print("per sample " + "   ".join(f"{label[arm]} " + ", ".join(f"{p}/{n}" for _, (p, n) in sorted(per_sample[arm].items()))
                                     for arm in present))
print(f"{summary}   input tokens {tokens:,}   workspace {W}")

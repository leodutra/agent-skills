#!/usr/bin/env python3
"""Verify the checks skills/rust-type-driven/SKILL.md tells projects to run, exactly as the skill prints them.

Each part copies the config blocks out of SKILL.md into a scratch project built from fixtures/<part>/, runs
the tool, and compares what it reports with the fixtures' markers: a line that must be flagged ends with a
comment `expect: <rule>[, <rule>...]` (a rule repeated once per finding on that line). Every other line is
clean or a near miss, and must not be flagged. Exit 0 when every part matches, 1 otherwise.

    verify.py [part ...]        parts: clippy, ast-grep, dependencies (default: all)

Tools come from PATH: put release binaries that are not installed first on it, e.g. PATH=/tmp/tools:$PATH.
"""
import collections
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.join(HERE, "..", "..", "skills", "rust-type-driven", "SKILL.md")
EXPECT = re.compile(r"(?://|#)\s*expect:\s*(.+?)\s*$")


def blocks(lang):
    """Fenced blocks of one language from the skill, as (first line, body)."""
    text = open(SKILL).read()
    return [(b.split("\n", 1)[0], b) for b in re.findall(rf"```{lang}\n(.*?)```", text, re.S)]


def expected(root):
    """The expect markers under root, as a multiset of (relative file, 1-based line, rule)."""
    out = collections.Counter()
    for folder, _, files in os.walk(root):
        for name in (n for n in files if n.endswith((".rs", ".toml"))):
            path = os.path.join(folder, name)
            for n, line in enumerate(open(path, encoding="utf-8"), 1):
                m = EXPECT.search(line)
                if m:
                    for rule in m.group(1).split(","):
                        out[(os.path.relpath(path, root), n, rule.strip())] += 1
    return out


def report(part, want, got):
    missing, extra = want - got, got - want
    for (f, n, rule), k in sorted(missing.items()):
        print(f"  {part}: MISSED  {f}:{n} {rule}" + (f" x{k}" if k > 1 else ""))
    for (f, n, rule), k in sorted(extra.items()):
        print(f"  {part}: EXTRA   {f}:{n} {rule}" + (f" x{k}" if k > 1 else ""))
    ok = not missing and not extra
    print(f"{part}: {'ok' if ok else 'FAIL'} ({sum(got.values())} findings, {sum(want.values())} expected)")
    return ok


def scratch(part):
    root = tempfile.mkdtemp(prefix=f"rtd-{part}-")
    shutil.copytree(os.path.join(HERE, "fixtures", part), root, dirs_exist_ok=True)
    return root


def check_clippy():
    """The Cargo.toml lints and clippy.toml of Enforce with Tools, on a crate with one violation per lint."""
    root = scratch("clippy")
    toml = [body for first, body in blocks("toml")]
    lints = next(b for b in toml if b.startswith("# Cargo.toml"))
    config = next(b for b in toml if b.startswith("# clippy.toml"))
    with open(os.path.join(root, "Cargo.toml"), "w") as f:
        f.write('[package]\nname = "fixture"\nversion = "0.1.0"\nedition = "2024"\n\n' + lints.split("\n", 1)[1])
    with open(os.path.join(root, "clippy.toml"), "w") as f:
        f.write(config.split("\n", 1)[1])
    want = expected(root)  # before the build, which fills target/
    run = subprocess.run(["cargo", "clippy", "--quiet", "--all-targets", "--message-format=json", "--", "-D", "warnings"],
                         cwd=root, capture_output=True, text=True, env={**os.environ, "CARGO_TARGET_DIR": os.path.join(root, "target")})
    got, seen = collections.Counter(), set()
    for line in run.stdout.splitlines():
        msg = json.loads(line)
        if msg.get("reason") != "compiler-message" or not (msg["message"].get("code") or {}).get("code"):
            continue
        span = next((s for s in msg["message"]["spans"] if s["is_primary"]), None)
        if not span:
            continue
        key = (span["file_name"], span["line_start"], msg["message"]["code"]["code"].removeprefix("clippy::"))
        if key not in seen:  # the lib and lib-test targets report the same finding twice
            seen.add(key)
            got[key] += 1
    return report("clippy", want, got)


def check_ast_grep():
    """sgconfig.yml and the .ast-grep/rules files of Enforce with Tools, on a tree with every rule's cases."""
    root = scratch("ast-grep")
    for first, body in blocks("yaml"):
        m = re.match(r"# (sgconfig\.yml|\.ast-grep/rules/[\w-]+\.yml)", first)
        if m:
            path = os.path.join(root, m.group(1))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(body)
    tool = os.environ.get("AST_GREP", "ast-grep")
    run = subprocess.run([tool, "scan", "--json=compact"], cwd=root, capture_output=True, text=True)
    got = collections.Counter((d["file"], d["range"]["start"]["line"] + 1, d["ruleId"]) for d in json.loads(run.stdout or "[]"))
    ok = report("ast-grep", expected(root), got)
    if got and run.returncode == 0:
        print("ast-grep: FAIL (findings, but `ast-grep scan` exited 0, so it would not gate CI)")
        ok = False
    return ok


def check_dependencies():
    """The two commands under Dependencies, run as the skill prints them, on a crate with each case."""
    root = scratch("dependencies")
    section = open(SKILL).read().split("### Dependencies", 1)[1]
    commands = re.search(r"```bash\n(.*?)```", section, re.S).group(1)
    approved = next(l for l in commands.splitlines() if l.startswith("cargo metadata"))
    machete = next(l for l in commands.splitlines() if l.startswith("cargo machete"))
    manifest = open(os.path.join(root, "Cargo.toml")).read().splitlines()
    line_of, table = {}, ""
    for n, l in enumerate(manifest, 1):  # a dependency's own line, in a dependency table only
        if l.startswith("["):
            table = l
        elif table.endswith("dependencies]") and "metadata" not in table and re.match(r"\S+\s*=", l):
            line_of[re.match(r"(\S+)\s*=", l).group(1)] = n
    got = collections.Counter()
    a = subprocess.run(["bash", "-c", approved], cwd=root, capture_output=True, text=True)
    for dep in re.findall(r"^\S+: (\S+) \(", a.stdout, re.M):
        got[("Cargo.toml", line_of[dep], "unapproved-dependency")] += 1
    m = subprocess.run(["bash", "-c", machete], cwd=root, capture_output=True, text=True)
    for dep in re.findall(r"^\t(\S+)$", m.stdout, re.M):
        got[("Cargo.toml", line_of[dep], "unused-dependency")] += 1
    ok = report("dependencies", expected(root), got)
    for name, run in (("approval check", a), ("cargo machete", m)):
        if run.returncode == 0:
            print(f"dependencies: FAIL ({name} exited 0 on findings, so it would not gate CI)")
            ok = False
    return ok


PARTS = {"clippy": check_clippy, "ast-grep": check_ast_grep, "dependencies": check_dependencies}

if __name__ == "__main__":
    wanted = sys.argv[1:] or list(PARTS)
    results = [PARTS[p]() for p in wanted]
    sys.exit(0 if all(results) else 1)

#!/usr/bin/env python3
"""Mechanical graders 01 and 02 of the code-writing evals (evals/*/graders/0[12]-*.md): cargo test as
delivered, and clippy -D warnings with the CURRENT skill's lints.toml and clippy.toml swapped in for
whatever lint config the run used, so every skill version is judged by the same rules.
Usage: grade_cargo.py <run outputs dir>; prints one JSON object. Needs cargo (and the network once)."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

SKILL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "skills", "rust-type-driven")
outputs = sys.argv[1]
result = {}


def run(cmd, cwd):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=900)
    tail = "\n".join(l for l in (p.stdout + p.stderr).splitlines() if l.startswith(("error", "test result")))[-1500:]
    return p.returncode == 0 and "unknown lint" not in p.stderr, tail


if not os.path.exists(os.path.join(outputs, "Cargo.toml")):
    print(json.dumps({"error": "no Cargo.toml"}))
    sys.exit(0)

work = tempfile.mkdtemp(prefix="grade-")
shutil.copytree(outputs, work, dirs_exist_ok=True, ignore=shutil.ignore_patterns("target"))
clippy = ["cargo", "clippy", "--quiet", "--all-targets", "--", "-D", "warnings"]
result["test_passed"], result["test_tail"] = run(["cargo", "test", "--quiet"], work)
result["clippy_as_delivered"], result["clippy_as_delivered_tail"] = run(clippy, work)

# Swap in the current lint set: drop every [lints...] / [workspace.lints...] table, append the skill's.
manifest = os.path.join(work, "Cargo.toml")
text = re.sub(r"(?ms)^\[(?:workspace\.)?lints(?:\.[a-z]+)?\]\n.*?(?=^\[|\Z)", "", open(manifest).read())
open(manifest, "w").write(text.rstrip() + "\n\n" + open(os.path.join(SKILL, "assets", "lints.toml")).read())
for root, _, files in os.walk(work):
    for f in files:
        if f in ("clippy.toml", ".clippy.toml") and "target" not in root:
            os.remove(os.path.join(root, f))
shutil.copy(os.path.join(SKILL, "assets", "clippy.toml"), work)
result["clippy_current_lints"], result["clippy_current_lints_tail"] = run(clippy, work)
shutil.rmtree(work, ignore_errors=True)
print(json.dumps(result))

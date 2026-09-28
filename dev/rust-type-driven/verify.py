#!/usr/bin/env python3
"""Verify the lint configuration skills/rust-type-driven ships, and its template, with the stock toolchain.

    python3 dev/rust-type-driven/verify.py

clippy: copies assets/lints.toml and assets/clippy.toml into a crate built from fixtures/clippy/ and runs
clippy. A line that must be flagged ends with `expect: <lint>[, <lint>...]` (a lint repeated once per
finding on that line); every other line is clean or a near miss and must not be flagged.

template: builds a crate from references/newtypes.md's template (the `// src/...` blocks) around
fixtures/template/, with the skill's lints, and requires cargo fmt --check, clippy and cargo test to pass.

Exit 0 when every part passes, 1 otherwise. Needs only cargo, rustfmt and clippy (and the network the
first time, for the template's crates).
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
SKILL_DIR = os.path.join(HERE, "..", "..", "skills", "rust-type-driven")
LINTS = os.path.join(SKILL_DIR, "assets", "lints.toml")
CLIPPY = os.path.join(SKILL_DIR, "assets", "clippy.toml")
REFERENCE = os.path.join(SKILL_DIR, "references", "newtypes.md")
EXPECT = re.compile(r"//\s*expect:\s*(.+?)\s*$")


def scratch(part):
    root = tempfile.mkdtemp(prefix=f"rtd-{part}-")
    shutil.copytree(os.path.join(HERE, "fixtures", part), root, dirs_exist_ok=True)
    return root


def adopt(root, manifest):
    """Cargo.toml as manifest plus the skill's lints, and the skill's clippy.toml, as a project adopts them."""
    with open(os.path.join(root, "Cargo.toml"), "w") as f:
        f.write(manifest + "\n" + open(LINTS).read())
    shutil.copy(CLIPPY, os.path.join(root, "clippy.toml"))


def expected(root):
    """The fixture's expect markers, as a multiset of (file, 1-based line, lint)."""
    out = collections.Counter()
    for n, line in enumerate(open(os.path.join(root, "src", "lib.rs"), encoding="utf-8"), 1):
        for lint in (m.group(1).split(",") if (m := EXPECT.search(line)) else []):
            out[("src/lib.rs", n, lint.strip())] += 1
    return out


def check_clippy():
    """assets/lints.toml and assets/clippy.toml, on a crate with one violation per lint and near misses."""
    root = scratch("clippy")
    adopt(root, '[package]\nname = "fixture"\nversion = "0.1.0"\nedition = "2024"\n')
    want = expected(root)  # before the build, which fills target/
    run = subprocess.run(["cargo", "clippy", "--quiet", "--all-targets", "--message-format=json", "--", "-D", "warnings"],
                         cwd=root, capture_output=True, text=True)
    got, seen = collections.Counter(), set()
    for line in run.stdout.splitlines():
        msg = json.loads(line)
        if msg.get("reason") != "compiler-message" or not (msg["message"].get("code") or {}).get("code"):
            continue
        span = next((s for s in msg["message"]["spans"] if s["is_primary"]), None)
        if not span:
            continue
        key = (span["file_name"], span["line_start"], msg["message"]["code"]["code"].removeprefix("clippy::"))
        if (key, span["column_start"]) not in seen:  # the lib and lib-test targets report the same finding twice
            seen.add((key, span["column_start"]))
            got[key] += 1
    for tag, diff in (("MISSED", want - got), ("EXTRA ", got - want)):
        for (f, n, lint), k in sorted(diff.items()):
            print(f"  clippy: {tag} {f}:{n} {lint}" + (f" x{k}" if k > 1 else ""))
    ok = want == got
    print(f"clippy: {'ok' if ok else 'FAIL'} ({sum(got.values())} findings, {sum(want.values())} expected)")
    return ok


def check_template():
    """The template in references/newtypes.md, with the skill's lints: fmt, clippy and its tests must all pass."""
    root = scratch("template")
    for path, body in re.findall(r"```rust\n// (src/\S+)\n(.*?)```", open(REFERENCE).read(), re.S):
        with open(os.path.join(root, path), "w") as f:
            f.write(body)
    adopt(root, open(os.path.join(root, "Cargo.toml")).read())
    ok = True
    for command in ("cargo fmt --check", "cargo clippy --quiet --all-targets -- -D warnings", "cargo test --quiet"):
        run = subprocess.run(command.split(), cwd=root, capture_output=True, text=True)
        if run.returncode != 0:
            print(f"template: FAIL ({command}):\n" + (run.stdout + run.stderr)[-2000:])
            ok = False
    print(f"template: {'ok' if ok else 'FAIL'} (fmt, clippy, test)")
    return ok


if __name__ == "__main__":
    sys.exit(0 if all([check_clippy(), check_template()]) else 1)  # a list, so both always run

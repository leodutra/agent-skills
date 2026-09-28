#!/usr/bin/env python3
"""Smoke test for skills/rust-type-driven: build references/newtypes.md's template with the skill's
assets/lints.toml and assets/clippy.toml; cargo fmt --check, clippy -D warnings and test must pass.
A lint clippy no longer knows fails it too (clippy itself only warns: unknown_lints ignores -D warnings). Needs only cargo (and the network once, for crates)."""
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.join(HERE, "..", "..", "skills", "rust-type-driven")

root = tempfile.mkdtemp(prefix="rtd-template-")
shutil.copytree(os.path.join(HERE, "fixtures", "template"), root, dirs_exist_ok=True)
for path, body in re.findall(r"```rust\n// (src/\S+)\n(.*?)```", open(os.path.join(SKILL, "references", "newtypes.md")).read(), re.S):
    with open(os.path.join(root, path), "w") as f:
        f.write(body)
with open(os.path.join(root, "Cargo.toml"), "a") as f:
    f.write("\n" + open(os.path.join(SKILL, "assets", "lints.toml")).read())
shutil.copy(os.path.join(SKILL, "assets", "clippy.toml"), root)

failed = False
for command in ("cargo fmt --check", "cargo clippy --quiet --all-targets -- -D warnings", "cargo test --quiet"):
    run = subprocess.run(command.split(), cwd=root, capture_output=True, text=True)
    if run.returncode or "unknown lint" in run.stderr:
        print(f"FAIL {command}:\n" + (run.stdout + run.stderr)[-2000:])
        failed = True
print("FAIL" if failed else "ok (fmt, clippy, test)")
sys.exit(failed)

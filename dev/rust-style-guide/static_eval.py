#!/usr/bin/env python3
"""Check enforced lint rules; --audit-gaps reports known review-only blind spots separately."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


HERE = Path(__file__).resolve().parent
SKILL = HERE.parent.parent / "skills" / "rust-style-guide" / "assets"
EXPECTED = {
    "clippy::let_underscore_future",
    "clippy::iter_over_hash_type",
    "clippy::exit",
    "clippy::dbg_macro",
    "clippy::print_stdout",
    "clippy::print_stderr",
    "clippy::disallowed_methods",
}

BAD = """
use std::collections::HashMap;

pub async fn forgotten() {
    let _ = std::future::ready(());
}

pub fn payout_order(amounts: &HashMap<u32, u64>) -> Vec<u32> {
    let mut order = Vec::new();
    for key in amounts.keys() {
        order.push(*key);
    }
    order
}

pub fn terminate() -> ! {
    std::process::exit(1)
}

pub fn hard_abort() -> ! {
    std::process::abort()
}

pub fn debug_output() {
    dbg!("trace");
    println!("output");
    eprintln!("error");
}
"""

GOOD = """
use std::collections::BTreeMap;

pub async fn completed() {
    std::future::ready(()).await;
}

pub fn payout_order(amounts: &BTreeMap<u32, u64>) -> Vec<u32> {
    amounts.keys().copied().collect()
}
"""

# These are valid Rust that violates a guide rule without tripping the named lint. The optional
# audit reports them as uncovered; they are not passing cases in the lint enforcement check.
REVIEW_GAPS = {
    "hash iterator chain": (
        "clippy::iter_over_hash_type",
        "pub fn x(m: &std::collections::HashMap<u8, u8>) -> Vec<u8> { m.keys().copied().collect() }",
    ),
    "private unit error": (
        "clippy::result_unit_err",
        "fn x() -> Result<(), ()> { Err(()) } pub fn y() -> bool { x().is_err() }",
    ),
    "source converted to text": (
        "clippy::map_err_ignore",
        'pub fn x() -> Result<(), String> { "bad".parse::<u8>().map(|_| ()).map_err(|e| e.to_string()) }',
    ),
    "future in named underscore binding": (
        "clippy::let_underscore_future",
        "pub fn x() { let _future = std::future::ready(()); }",
    ),
    "result in named underscore binding": (
        "clippy::let_underscore_must_use",
        "pub fn x() { let _ignored = Err::<(), u8>(1); }",
    ),
    "explicit result drop": (
        "clippy::let_underscore_must_use",
        "pub fn x() { drop(Err::<(), u8>(1)); }",
    ),
    "assert on external input": (
        "clippy::panic",
        "pub fn x(input: bool) { assert!(input); }",
    ),
    "private type without Debug": (
        "missing_debug_implementations",
        "struct Port(std::num::NonZeroU8); pub fn x(n: u8) -> Option<u8> { std::num::NonZeroU8::new(n).map(|n| Port(n).0.get()) }",
    ),
}


def run_clippy(root: Path, source: str, deny_warnings: bool) -> tuple[int, set[str], str]:
    (root / "src").mkdir(parents=True)
    (root / "src" / "lib.rs").write_text(source)
    (root / "Cargo.toml").write_text(
        '[package]\nname = "lint_probe"\nversion = "0.1.0"\nedition = "2024"\n\n'
        + (SKILL / "lints.toml").read_text()
    )
    shutil.copy(SKILL / "clippy.toml", root / "clippy.toml")
    cmd = ["cargo", "clippy", "--offline", "--all-targets", "--message-format=json"]
    if deny_warnings:
        cmd += ["--", "-D", "warnings"]
    result = subprocess.run(cmd, cwd=root, capture_output=True, text=True, check=False)
    errors = set()
    for line in result.stdout.splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if item.get("reason") != "compiler-message":
            continue
        message = item["message"]
        if message.get("level") == "error" and message.get("code"):
            errors.add(message["code"]["code"])
    return result.returncode, errors, result.stderr


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-gaps", action="store_true", help="report unenforced guide patterns")
    args = parser.parse_args()
    if not shutil.which("cargo"):
        print("FAIL: cargo is unavailable")
        return 1
    with tempfile.TemporaryDirectory(prefix="rsg-static-") as temp:
        root = Path(temp)
        bad_code, errors, bad_stderr = run_clippy(root / "bad", BAD, False)
        good_code, good_errors, good_stderr = run_clippy(root / "good", GOOD, True)
        missing = EXPECTED - errors
        if bad_code == 0 or missing or good_code != 0 or good_errors or "unknown lint" in bad_stderr + good_stderr:
            print(f"FAIL: missing denied lints: {sorted(missing)}")
            print(f"planted exit: {bad_code}; clean exit: {good_code}; clean errors: {sorted(good_errors)}")
            print((bad_stderr + good_stderr)[-1500:])
            return 1
        if args.audit_gaps:
            uncovered = []
            changed = []
            for index, (name, (lint, source)) in enumerate(REVIEW_GAPS.items()):
                code, seen, _ = run_clippy(root / f"gap-{index}", source, False)
                if code == 0 and lint not in seen:
                    uncovered.append(name)
                else:
                    changed.append(f"{name}: exit {code}, diagnostics {sorted(seen)}")
            print(f"lint enforcement: {len(EXPECTED)} planted lints denied; clean fixture passes")
            print(f"review-only patterns still unenforced: {len(uncovered)}")
            for name in uncovered:
                print(f"  - {name}")
            for item in changed:
                print(f"coverage changed; inspect: {item}")
            return 1 if uncovered or changed else 0
    print(f"ok ({len(EXPECTED)} planted lints denied; clean fixture passes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

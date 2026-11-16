#!/usr/bin/env python3
"""Tier 1 of the per-rule suite: the lints hold what the guide says they hold.

Every sample in rules/lints/ is clippy'd with the skill's assets/lints.toml and assets/clippy.toml:
- `<lint>[.<variant>].bad.rs` starts with `// expect: <lint> [<path>]` and must raise that lint (with
  that path in the message, for clippy.toml's disallowed-* entries) and nothing it doesn't declare on
  an optional `// also: <lint> ...` line;
- every `*.good.rs` must raise nothing (the guide's fix, and the Allowed entries the lints touch);
- coverage: every lint in lints.toml and every disallowed-* path in clippy.toml has a bad sample, and
  every lint has `<lint>.good.rs`.
bin/ holds samples that must be a binary's main; unsafe/ is a crate with unsafe_code lowered to deny,
as lints.toml's comment allows. The review-only patterns (what slips past a lint that looks like it
holds) are tier 3's bad samples: rules.py checks that no lint catches them.
Needs cargo, and crates.io once for the probe's dependencies.
"""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import tomllib

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent.parent / "skills" / "rust-style-guide" / "assets"
SAMPLES = HERE / "rules" / "lints"
WORK = Path(tempfile.gettempdir()) / "rsg-static-eval"  # kept between runs: lockfile and target dir
DEPS = """
anyhow = "1"
eyre = "0.6"
chrono = { version = "0.4", default-features = false, features = ["clock", "std"] }
rand = "0.9"
uuid = { version = "1", features = ["v4", "v7"] }
"""
UNSAFE_DEPS = """
ctor = "0"
dtor = "0"
"""

# SKILL.md's "The lints hold:" list, item by item (split at `;`), with the lints that keep each promise.
# The map lives here, not in SKILL.md, so the guide stays prose; the check fails on an unmapped item.
D = "clippy::disallowed_"
PROMISES = {
    "wildcard arms": ["clippy::wildcard_enum_match_arm", "clippy::match_wildcard_for_single_variants"],
    "unwrap/expect/panic/todo/unimplemented/unreachable outside tests": [
        "clippy::unwrap_used", "clippy::expect_used", "clippy::panic", "clippy::todo", "clippy::unimplemented",
        "clippy::unreachable"],
    "unsafe, undocumented unsafe, several unsafe operations per block and an `unsafe fn` without `# Safety`": [
        "unsafe_code", "unsafe_op_in_unsafe_fn", "clippy::undocumented_unsafe_blocks",
        "clippy::multiple_unsafe_ops_per_block", "clippy::missing_safety_doc"],
    "a hand-written `Default` a derive would produce": ["clippy::derivable_impls"],
    "`Clone` on `Copy`": ["clippy::expl_impl_clone_on_copy"],
    "`Hash`/`Ord` derived beside a hand-written `PartialEq`/`PartialOrd`": [
        "clippy::derived_hash_with_manual_eq", "clippy::derive_ord_xor_partial_ord"],
    "`#[ctor]`/`#[dtor]`": [f"{D}macros ctor::ctor", f"{D}macros dtor::dtor"],
    "public types missing `Debug`": ["missing_debug_implementations"],
    "`PartialEq` that could be `Eq`": ["clippy::derive_partial_eq_without_eq"],
    "infallible `TryFrom`": ["clippy::infallible_try_from"],
    "public `Result<_, ()>`": ["clippy::result_unit_err"],
    "never-failing `Result`": ["clippy::unnecessary_wraps"],
    "mixed `pub` fields": ["clippy::partial_pub_fields"],
    "`Option<Option<T>>`": ["clippy::option_option"],
    "non-`Send` futures": ["clippy::future_not_send"],
    "locks across `.await`": ["clippy::await_holding_lock", "clippy::await_holding_refcell_ref"],
    ">3 bools": ["clippy::struct_excessive_bools", "clippy::fn_params_excessive_bools"],
    "glob imports": ["clippy::wildcard_imports"],
    "`for_each`": ["clippy::needless_for_each"],
    "needless pass by value": ["clippy::needless_pass_by_value"],
    "`&Option` params": ["clippy::ref_option"],
    "redundant clones": ["clippy::redundant_clone"],
    "`map_err(|_| …)`": ["clippy::map_err_ignore"],
    "dropped `Result` or future": [
        "clippy::unused_result_ok", "clippy::let_underscore_must_use", "clippy::let_underscore_future"],
    "`assert!(r.is_err())`": ["clippy::assertions_on_result_states"],
    "bare `#[allow]`, missing reasons": ["clippy::allow_attributes", "clippy::allow_attributes_without_reason"],
    "`anyhow`/`eyre`": [f"{D}types anyhow::Error", f"{D}types anyhow::Result", f"{D}types eyre::Report",
                        f"{D}types eyre::Result"],
    "`Cell`/`RefCell`/`Mutex`/`RwLock`": [f"{D}types std::cell::Cell", f"{D}types std::cell::RefCell",
                                          f"{D}types std::sync::Mutex", f"{D}types std::sync::RwLock"],
    "banned clock/`rand`/`uuid` calls": [
        f"{D}methods std::time::SystemTime::now", f"{D}methods std::time::Instant::now",
        f"{D}methods chrono::Utc::now", f"{D}methods rand::random", f"{D}methods rand::rng",
        f"{D}methods rand::thread_rng", f"{D}methods uuid::Uuid::new_v4", f"{D}methods uuid::Uuid::now_v7"],
    "`catch_unwind`": [f"{D}methods std::panic::catch_unwind"],
    "reading a poisoned lock": [f"{D}methods std::sync::PoisonError::into_inner",
                                f"{D}methods std::sync::PoisonError::get_ref",
                                f"{D}methods std::sync::PoisonError::get_mut"],
    "`process::abort`/`exit`": [f"{D}methods std::process::abort", "clippy::exit"],
    "lossy `as`": ["clippy::cast_possible_truncation", "clippy::cast_sign_loss", "clippy::cast_possible_wrap"],
    "`&s[a..b]` on `str`": ["clippy::string_slice"],
    "hash `for` loops": ["clippy::iter_over_hash_type"],
    "debug and print macros": ["clippy::dbg_macro", "clippy::print_stdout", "clippy::print_stderr"],
}

def header(path: Path) -> tuple[str, str | None, set[str]]:
    lines = path.read_text().splitlines()
    match = re.fullmatch(r"// expect: (\S+)(?: (\S+))?", lines[0]) if lines else None
    if not match:
        sys.exit(f"FAIL {path.relative_to(HERE)}: a bad sample starts with `// expect: <lint> [<path>]`")
    also = next((line[len("// also: "):].split() for line in lines[1:3] if line.startswith("// also: ")), [])
    return match[1], match[2], set(also)


def module(path: Path) -> str:
    return re.sub(r"\W", "_", path.name.removesuffix(".rs"))


def member(work: Path, name: str, lints: str, deps: str = "", body: str = "") -> None:
    root = work / name
    (root / "src").mkdir(parents=True, exist_ok=True)
    (root / "Cargo.toml").write_text(
        f'[package]\nname = "{name}"\nversion = "0.0.0"\nedition = "2024"\npublish = false\n{body}'
        f"\n[dependencies]{deps}\n{lints}"
    )


def write_workspace() -> None:
    lints = (ASSETS / "lints.toml").read_text()
    unsafe_lints = lints.replace('unsafe_code = "forbid"', 'unsafe_code = "deny"')
    if unsafe_lints == lints:
        sys.exit('FAIL: lints.toml no longer has unsafe_code = "forbid"; update the unsafe probe')
    members = {"probe": SAMPLES.glob("*.rs"), "probe_unsafe": (SAMPLES / "unsafe").glob("*.rs")}
    for name, files in members.items():
        member(WORK, name, *((unsafe_lints, UNSAFE_DEPS) if name == "probe_unsafe" else (lints, DEPS)), body="")
        mods = "".join(f'#[path = "{f}"]\npub mod {module(f)};\n' for f in sorted(files))
        (WORK / name / "src" / "lib.rs").write_text(mods)
    bins = "".join(
        f'\n[[bin]]\nname = "{module(f)}"\npath = "{f}"\n' for f in sorted((SAMPLES / "bin").glob("*.rs"))
    )
    member(WORK, "probe_bins", lints, body="autobins = false\n" + bins)
    (WORK / "probe_bins" / "src" / "lib.rs").write_text("")
    names = list(members) + ["probe_bins"]
    (WORK / "Cargo.toml").write_text(
        f'[workspace]\nresolver = "3"\nmembers = {json.dumps(names)}\n'
    )
    (WORK / "clippy.toml").write_text((ASSETS / "clippy.toml").read_text())


def clippy(work: Path) -> tuple[dict[str, set[tuple[str, str]]], list[str], set[tuple[str, bool]]]:
    """Diagnostics per source file as (code, message); the ones no sample file explains; and the lib
    units cargo finished checking, as (crate, is_test). A unit that fails (a compile error, a denied
    lint) or never ran is missing from the last, so "no diagnostics" alone never means clean."""
    run = subprocess.run(
        ["cargo", "clippy", "--workspace", "--all-targets", "--keep-going", "--message-format=json"],
        cwd=work, capture_output=True, text=True, check=False,
    )
    seen: dict[str, set[tuple[str, str]]] = {}
    stray = []
    checked = set()
    for line in run.stdout.splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if item.get("reason") == "compiler-artifact" and "lib" in item["target"]["kind"]:
            checked.add((item["target"]["name"], item["profile"]["test"]))
        if item.get("reason") != "compiler-message":
            continue
        message = item["message"]
        code = (message.get("code") or {}).get("code", "")
        # A lint whose diagnostic carries an error code (unsafe_op_in_unsafe_fn: E0133) names itself in a note.
        if named := re.search(r"requested on the command line with `-[DFW] ([\w:-]+)`", message["rendered"]):
            code = named[1].replace("-", "_")
        primary = [s for s in message.get("spans", []) if s.get("is_primary")]
        if not primary:
            if not re.match(r"aborting due to|\d+ warnings? emitted|For more information|Some errors have detailed", message["message"]):
                stray.append(message["rendered"].strip()[:300])
            continue
        file = str(work / primary[0]["file_name"])  # relative to the workspace root, or absolute
        seen.setdefault(str(Path(file).resolve()), set()).add((code or message["level"], message["message"]))
    if run.returncode and not seen and not stray:
        stray.append(run.stderr[-1500:])
    for line in run.stderr.splitlines():
        if "unknown lint" in line or "error reading Clippy" in line or line.startswith("error: failed"):
            stray.append(line)
    return seen, stray, checked


def coverage() -> list[str]:
    lints = tomllib.loads((ASSETS / "lints.toml").read_text())["lints"]
    config = tomllib.loads((ASSETS / "clippy.toml").read_text())
    wanted = {name: None for name in lints["rust"]} | {f"clippy::{name}": None for name in lints["clippy"]}
    paths = {
        (f"clippy::{key.replace('-', '_')}", entry["path"])
        for key in ("disallowed-types", "disallowed-methods", "disallowed-macros")
        for entry in config.get(key, [])
    }
    bad = {header(f)[:2] for f in SAMPLES.rglob("*.bad.rs")}
    bad_lints = {lint for lint, _ in bad}
    goods = {f.name.split(".")[0] for f in SAMPLES.rglob("*.good.rs") if f.name.count(".") == 2}
    problems = [f"no bad sample for {lint}" for lint in wanted if lint not in bad_lints]
    problems += [f"no bad sample for {lint} {path}" for lint, path in sorted(paths - bad)]
    problems += [f"no good sample for {lint}" for lint in wanted if lint.removeprefix("clippy::") not in goods]
    problems += [f"{lint} {path or ''}: not in lints.toml/clippy.toml" for lint, path in bad
                 if lint not in wanted or (path and (lint, path) not in paths)]
    return problems + promises(set(wanted), paths)


def promises(wanted: set[str], paths: set[tuple[str, str]]) -> list[str]:
    """SKILL.md's "The lints hold:" list against PROMISES, and PROMISES against the lint config."""
    text = (ASSETS.parent / "SKILL.md").read_text()
    listed = re.search(r"The lints hold:(.*?)\n\n", text, re.S)
    if not listed:
        return ['SKILL.md has no "The lints hold:" list']
    items = [i.strip() for i in listed[1].replace("\n", " ").strip().rstrip(".").split(";")]
    problems = [f"SKILL.md promises {i!r}, which PROMISES doesn't map to a lint" for i in items if i not in PROMISES]
    problems += [f"PROMISES maps {i!r}, which SKILL.md no longer lists" for i in PROMISES if i not in items]
    entries = [tuple(e.split(" ", 1)) if " " in e else (e, None) for es in PROMISES.values() for e in es]
    problems += [f"a promised lint isn't configured: {' '.join(filter(None, e))}" for e in entries
                 if e[0] not in wanted or (e[1] and e not in paths)]
    promised = {lint for lint, _ in entries}
    problems += [f"{lint} is configured but SKILL.md's list doesn't promise it" for lint in sorted(wanted - promised)]
    problems += [f"{lint} {path} is configured but SKILL.md's list doesn't promise it"
                 for lint, path in sorted(paths - set(entries))]
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.parse_args()
    problems = coverage()
    WORK.mkdir(exist_ok=True)
    write_workspace()
    seen, stray, _ = clippy(WORK)
    problems += [f"diagnostic outside the samples: {s}" for s in stray]

    samples = sorted(SAMPLES.rglob("*.rs"))
    known = {str(f.resolve()) for f in samples}
    problems += [f"diagnostic outside the samples: {file}: {sorted(found)}"
                 for file, found in seen.items() if file not in known]
    for f in samples:
        found = seen.get(str(f.resolve()), set())
        codes = {code for code, _ in found}
        name = str(f.relative_to(SAMPLES))
        if f.name.endswith(".good.rs"):
            if found:
                problems.append(f"{name}: good sample raised {sorted(found)}")
            continue
        lint, path, also = header(f)
        hit = any(code == lint and (path is None or f"`{path}`" in text) for code, text in found)
        if not hit:
            problems.append(f"{name}: expected {lint} {path or ''}, got {sorted(found) or 'nothing'}")
        if extra := codes - {lint} - also:
            problems.append(f"{name}: undeclared {sorted(extra)}")

    bad = sum(f.name.endswith(".bad.rs") for f in samples)
    if problems:
        print("FAIL\n" + "\n".join(f"- {p}" for p in problems))
        return 1
    print(f"ok ({bad} bad samples raise their lint, {len(samples) - bad} good samples are clean, coverage complete)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

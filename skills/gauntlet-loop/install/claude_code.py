#!/usr/bin/env python3
"""Wire the gauntlet loop into a target repository. The only file that knows how Claude Code is configured.

claude_code.py <repo>   copy the controller, hooks, policy and agent definitions; merge settings; write the manifest.
                        `gauntletctl detect` checks the installed files against it.

Idempotent: a second run changes nothing. Review the diff and check it in before a run; a rule counts as
enforced only when its hook was in checked-in settings before the run started.
"""
import hashlib
import json
import os
import shutil
import sys

SKILL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DEST = ".claude/hooks/gauntlet"


def hook(script, *extra):
    return {"type": "command", "command": "python3", "args": ["${CLAUDE_PROJECT_DIR}/" + DEST + "/" + script, *extra]}


# Registered in settings, not in agent frontmatter: frontmatter hooks are skipped in a folder whose trust
# dialog was never accepted (harness-claude-code.md, S1). Each script passes agents it is not for.
HOOKS = {
    "PreToolUse": [
        ("Read|Glob|Grep|Bash", "critic_blind.py"),
        ("Read|Glob|Grep|Edit|Write|Bash", "builder_boundary.py"),
        ("Edit|Write|Bash", "protect_floors.py"),
        ("Read|Glob|Grep|Edit|Write|Bash", "controller_only.py"),
        ("Edit|Write|Bash", "author_scope.py"),
    ],
    "SubagentStart": [("reader|reader-alt|editor|editor-fast|author", "attest.py", "--start")],
    "SubagentStop": [("reader|reader-alt|editor|editor-fast|author", "attest.py")],
}


def digest(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def copy_tree(src, dst, manifest, repo):
    for name in sorted(os.listdir(src)):
        s, d = os.path.join(src, name), os.path.join(dst, name)
        if os.path.isdir(s) or name == "__pycache__":
            continue
        os.makedirs(dst, exist_ok=True)
        shutil.copy(s, d)
        manifest.append(os.path.relpath(d, repo))


def union(ours, shipped):
    """Shipped keys merged under what is already there: lists gain missing entries, scalars are set, nothing is removed."""
    out = dict(ours)
    for k, v in shipped.items():
        if isinstance(v, dict):
            out[k] = union(out.get(k, {}), v)
        elif isinstance(v, list):
            out[k] = out.get(k, []) + [x for x in v if x not in out.get(k, [])]
        else:
            out[k] = v
    return out


def merge_settings(repo):
    path = os.path.join(repo, ".claude", "settings.json")
    settings = {}
    if os.path.exists(path):
        with open(path) as f:
            settings = json.load(f)
    for event, entries in HOOKS.items():
        groups = settings.setdefault("hooks", {}).setdefault(event, [])
        for matcher, *script in entries:
            group = next((g for g in groups if g.get("matcher") == matcher), None)
            if group is None:
                group = {"matcher": matcher, "hooks": []}
                groups.append(group)
            if hook(*script) not in group["hooks"]:
                group["hooks"].append(hook(*script))
    with open(os.path.join(SKILL, "permissions", "allowlist.json")) as f:
        shipped = json.load(f)
    settings = union(settings, {k: shipped[k] for k in ("permissions", "sandbox")})
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")


def install(repo):
    manifest = []
    dest = os.path.join(repo, DEST)
    copy_tree(os.path.join(SKILL, "bin"), dest, manifest, repo)
    copy_tree(os.path.join(SKILL, "hooks"), dest, manifest, repo)
    if os.path.isdir(os.path.join(SKILL, "policy")):
        copy_tree(os.path.join(SKILL, "policy"), os.path.join(dest, "policy"), manifest, repo)
    copy_tree(os.path.join(SKILL, "agents"), os.path.join(repo, ".claude", "agents"), manifest, repo)
    # A hook's first run leaves bytecode beside it; untracked, it reads as "not checked in" and `detect` says tier 3.
    with open(os.path.join(dest, ".gitignore"), "w") as f:
        f.write("__pycache__/\n")
    merge_settings(repo)
    with open(os.path.join(dest, "MANIFEST.sha256"), "w") as f:
        for rel in manifest:
            f.write(f"{digest(os.path.join(repo, rel))}  {rel}\n")


def main(argv):
    if len(argv) != 1 or not os.path.isdir(argv[0]):
        print(__doc__, file=sys.stderr)
        return 2
    install(os.path.realpath(argv[0]))
    print(f"installed into {argv[0]}: review the diff, check it in, then run {DEST}/gauntletctl")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

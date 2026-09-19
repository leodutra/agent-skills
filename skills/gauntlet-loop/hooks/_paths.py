"""Shared by every gauntlet hook: payload, path resolution, segment matching, bindings, deny-and-log."""
import json
import os
import re
import shlex
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SAFE = ("/dev/null",)


def payload():
    return json.load(sys.stdin)


def project():
    return os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def controller():
    """Installed, the controller sits beside the hooks; in the skill folder it is under bin/."""
    beside = os.path.join(HERE, "gauntletctl")
    return beside if os.path.exists(beside) else os.path.join(HERE, "..", "bin", "gauntletctl")


def policy():
    """The pinned policy: beside the hooks when installed, under policy/ in the skill folder."""
    for path in (os.path.join(HERE, "policy", "v1.json"), os.path.join(HERE, "..", "policy", "v1.json")):
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
    raise SystemExit("gauntlet hooks: policy/v1.json is missing beside them")


def resolve(path, base):
    """Absolute path with ~, .. and symlinks resolved first."""
    return os.path.realpath(os.path.join(base, os.path.expanduser(path)))


def inside(path, root):
    return path == root or path.startswith(root + os.sep)


def tree_of(path, trees, root):
    """The protected tree a path sits in, else None. A tree counts at the project root and at the root of a
    piece's worktree (.gauntlet/wt/<piece>/), so the copy inside a worktree is covered and docs/reference/ is not."""
    parts = os.path.relpath(path, root).split(os.sep)
    if parts[:2] == [".gauntlet", "wt"]:
        parts = parts[3:]
    for tree in trees:
        seg = tree.strip("/").split("/")
        if parts[:len(seg)] == seg:
            return tree
    return None


_WRITE_VERBS = re.compile(r"\b(rm|mv|cp|tee|touch|mkdir|rmdir|truncate|dd|ln|install|chmod|sed\s+-i|git\s+(checkout|restore|rm|mv|apply|stash|clean|reset))\b")
_REDIRECT = re.compile(r"(^|[\s\d)\"'])>{1,2}(?![&>])")  # a redirect to a file; not `=>`, `->` or `2>&1`


class _Writes:
    """Does a shell command write somewhere? A string match: redirects to /dev/null and fd duplications are not writes."""

    def search(self, command):
        command = re.sub(r"\d?>>?\s*/dev/null", " ", command)
        return _WRITE_VERBS.search(command) or _REDIRECT.search(command)


WRITES = _Writes()


def shell_base(command, root):
    """Where a command's relative paths resolve: the project root, or the directory a leading `cd` names."""
    m = re.match(r"\s*cd\s+(\S+)\s*(&&|;)", command)
    return resolve(m.group(1).strip("'\""), root) if m else root


def glob_base(pattern):
    """The literal directory prefix of a glob pattern."""
    keep = []
    for part in pattern.split("/"):
        if re.search(r"[*?\[{]", part):
            break
        keep.append(part)
    return "/".join(keep) or "."


def path_tokens(command):
    """Tokens of a shell command that look like paths. A string match, not a shell parser: Tier 2, never isolation."""
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        tokens = command.split()
    out = []
    for token in tokens:
        for part in token.split("="):
            if part not in SAFE and ("/" in part or part.startswith((".", "~"))):
                out.append(part)
    return out


def binding(agent_id, value=None):
    """What an agent is bound to (a pair or a worktree). Recorded once; the first write wins."""
    path = os.path.join(project(), ".gauntlet", "private", "bindings", re.sub(r"\W", "_", agent_id or "none"))
    if value is None:
        if not os.path.exists(path):
            return None
        with open(path) as f:
            return f.read().strip()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        with open(path, "x") as f:
            f.write(value)
    except FileExistsError:
        pass
    return binding(agent_id)


def allow(updated_input=None):
    if updated_input:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "updatedInput": updated_input}}))
    sys.exit(0)


def deny(reason, event, p, path):
    """Deny the call, and log the block through the log's single writer. Logging never stops a deny."""
    fields = {"agent_id": p.get("agent_id"), "agent_type": p.get("agent_type"), "artifact": path, "note": p.get("tool_name")}
    try:
        subprocess.run([sys.executable, controller(), "log-block", event, json.dumps(fields)],
                       cwd=project(), capture_output=True, timeout=10)
    except Exception:
        pass
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))
    sys.exit(0)

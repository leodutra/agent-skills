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


_WRITE_VERBS = re.compile(r"\b(rm|mv|cp|tee|touch|mkdir|rmdir|truncate|dd|ln|install|chmod|sed\s+-i|git\s+(clone|checkout|restore|rm|mv|apply|stash|clean|reset))\b")
_REDIRECT = re.compile(r"(^|[\s\d)\"'])>{1,2}(?![&>])")  # a redirect to a file; not `=>`, `->` or `2>&1`


def _no_heredoc_bodies(command):
    """A here-document's body is data the shell passes on, not shell: keep the line that opens it, drop the body."""
    return re.sub(r"(<<-?\s*(['\"]?)(\w+)\2[^\n]*\n).*?(\n[ \t]*\3[ \t]*(?=\n|$)|$)", r"\1", command, flags=re.S)


def _shell_text(command):
    """What the shell itself reads as operators: no quoted strings, no here-document bodies."""
    return re.sub(r"'[^']*'|\"(?:\\.|[^\"\\])*\"", "''", _no_heredoc_bodies(command))


class _Writes:
    """Does a shell command write somewhere? A string match: redirects to /dev/null and fd duplications are not writes,
    and a `>` inside a quoted script or a here-document is not a redirect. Write verbs are matched on the raw command,
    so quoting a verb does not hide it."""

    def search(self, command):
        command = re.sub(r"\d?>>?\s*/dev/null", " ", command)
        return _WRITE_VERBS.search(command) or _REDIRECT.search(_shell_text(command))


WRITES = _Writes()


def shell_base(command, root):
    """Where a command's relative paths resolve: the project root, or the directory a leading `cd` names."""
    m = re.match(r"\s*cd\s+(\S+)\s*(&&|;)", command)
    return resolve(m.group(1).strip("'\""), root) if m else root


ALONE = " Run the controller alone on its line, with nothing chained to it, and each write as its own command."


def controller_alone(command):
    """The controller alone on its line: the one hand that writes the run's files, held to its own rules. Chained, the
    hooks cannot tell its arguments from the shell's, so a compound command gets the ordinary checks."""
    return bool(re.search(r"gauntletctl\S*\s+\w", command)) and not re.search(r"&&|\|\||[;|<>`]|\$\(", command)


def glob_base(pattern):
    """The literal directory prefix of a glob pattern."""
    keep = []
    for part in pattern.split("/"):
        if re.search(r"[*?\[{]", part):
            break
        keep.append(part)
    return "/".join(keep) or "."


_OPERAND_VERBS = ("rm", "mv", "cp", "tee", "touch", "mkdir", "rmdir", "truncate", "ln")


def path_tokens(command, base=None):
    """Tokens of a shell command that look like paths. Given a base, a bare word counts too when it exists there, takes a
    redirect, or is an operand of a plain write verb (`rm -rf heldout`, `> notes`, `touch new.js`).
    A string match, not a shell parser: Tier 2, never isolation."""
    try:
        lexer = shlex.shlex(_no_heredoc_bodies(command), posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        tokens = command.split()
    out, redirected, operand = [], False, False
    for token in tokens:
        if token in ("&&", "||", ";", "|", "&"):
            operand = False
        if "://" in token:  # a URL is not a path
            continue
        for part in re.split(r"[=:]", token):  # `a=b`, and a revision path such as `HEAD:heldout/x`
            if not part or part in SAFE:
                continue
            bare = base and (redirected or (operand and not part.startswith("-")) or os.path.lexists(os.path.join(base, part)))
            if "/" in part or part.startswith((".", "~")) or bare:
                out.append(part)
        redirected = token in (">", ">>")
        operand = operand or token in _OPERAND_VERBS
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

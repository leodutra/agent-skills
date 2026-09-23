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


_ALL_OPERANDS = ("rm", "tee", "touch", "mkdir", "rmdir", "truncate")
_LAST_OPERAND = ("mv", "cp", "ln", "install")
_GIT_WRITES = ("checkout", "restore", "rm", "mv", "apply", "stash", "clean", "reset", "clone")
_SEPARATORS = ("&&", "||", ";", "|", "&", "(", ")")


def write_targets(command, base):
    """The paths a shell command writes: redirect targets, the operands of a write verb (the last one of a copy or a
    move), a `sed -i` file, `dd of=`, a git path. A sed script or a file that is only read is not one. A string match
    like the rest: Tier 2, never isolation. A caller denies a target it cannot resolve (see unresolved)."""
    try:
        lexer = shlex.shlex(_no_heredoc_bodies(command), posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        tokens = command.split()
    out, words, skip = [], [], None

    def flush():
        if words:
            verb, args = words[0], [w for w in words[1:] if not w.startswith("-")]
            if verb in _ALL_OPERANDS:
                out.extend(args)
            elif verb in _LAST_OPERAND and args:
                out.append(args[-1])
            elif verb == "sed" and any(w.startswith("-i") or w == "--in-place" for w in words[1:]):
                out.extend(a for a in args if os.path.lexists(os.path.join(base, a)))  # the script is not a file
            elif verb == "dd":
                out.extend(w[3:] for w in words[1:] if w.startswith("of="))
            elif verb == "git" and args and args[0] in _GIT_WRITES:
                out.extend(a for a in args[1:] if "://" not in a and ("/" in a or a.startswith(".")))
        words.clear()

    for token in tokens:
        if skip:  # the word after a redirect: a target after `>`, a source after `<`, a descriptor after `>&`
            if skip == ">" and token not in SAFE:
                out.append(token)
            skip = None
        elif token in _SEPARATORS:
            flush()
        elif token in (">", ">>", ">|", "&>", "&>>", "<", "<<", "<<<", ">&", "<&"):
            if words and words[-1].isdigit():
                words.pop()  # `2>`: the descriptor is not an operand
            skip = ">" if token in (">", ">>", ">|", "&>", "&>>") else "<"
        else:
            words.append(token)
    flush()
    return out


def unresolved(target):
    """A target named through the shell (a variable, a substitution): the hook cannot say where it lands."""
    return "$" in target or "`" in target or (target.startswith("~") and not target.startswith("~/"))


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

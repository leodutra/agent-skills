"""Shared by every gauntlet hook: payload, path resolution, segment matching, bindings, deny-and-log."""
import fnmatch
import json
import os
import re
import shlex
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SAFE = ("/dev/null",)


def payload():
    """The hook's input. Each call also stamps the agent's activity where the sandboxed controller can read it: the
    sandbox hides the agents' transcripts from it, so this is how `next` tells a quiet agent from a working one (F45)."""
    p = json.load(sys.stdin)
    if p.get("agent_id") and os.path.isdir(os.path.join(project(), ".gauntlet")):
        try:
            beats = os.path.join(project(), ".gauntlet", "private", "activity")
            os.makedirs(beats, exist_ok=True)
            with open(os.path.join(beats, re.sub(r"\W", "_", p["agent_id"])), "a"):
                pass
            os.utime(os.path.join(beats, re.sub(r"\W", "_", p["agent_id"])))
        except OSError:
            pass
    return p


def project():
    """The project, even from inside a piece's worktree (F30)."""
    here = os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    return here.split(os.sep + os.path.join(".gauntlet", "wt") + os.sep)[0]


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




def _no_heredoc_bodies(command):
    """A here-document's body is data the shell passes on, not shell: keep the line that opens it, drop the body."""
    return re.sub(r"(<<-?\s*(['\"]?)(\w+)\2[^\n]*\n).*?(\n[ \t]*\3[ \t]*(?=\n|$)|$)", r"\1", command, flags=re.S)


def _shell_text(command):
    """What the shell itself reads as operators: no quoted strings, no here-document bodies."""
    return re.sub(r"'[^']*'|\"(?:\\.|[^\"\\])*\"", "''", _no_heredoc_bodies(command))


def variants(command):
    """The command with what the shell would put in its variables: one it sets itself (`S=/x; cat $S/a`), a loop's words
    (`for f in a b; do cat $f`), $TMPDIR and $HOME. One variant per loop word, so each value is judged; a variable it
    cannot know stays as written and is judged unresolved (F31). Single-quoted text is left as the shell leaves it."""
    tmp = os.environ.get("TMPDIR", "")
    values = {"HOME": [os.path.expanduser("~")], "TMPDIR": [tmp if "claude" in tmp else f"/tmp/claude-{os.getuid()}"]}
    for name, value in re.findall(r"(?:^|[\s;&|(])([A-Za-z_]\w*)=((?:\"[^\"]*\"|'[^']*'|[^\s;&|()])+)", command):
        values[name] = [value.strip("\"'")]
    for name, words in re.findall(r"\bfor\s+([A-Za-z_]\w*)\s+in\s+([^;\n]*?)\s*;\s*do\b", command):
        values[name] = [w.strip("\"'") for w in words.split()] or [""]
    out = [command]
    for _ in range(2):  # a value can name another variable (`f=$D/$s`): the second pass fills in what the first put in
        for name, options in reversed(list(values.items())):  # later ones first: a loop's list may use an earlier variable
            if any(re.search(rf"\$\{{?{name}\b", v) for v in out):
                pattern = re.compile(rf"'[^']*'|\$\{{{name}\}}|\${name}\b")
                out = [pattern.sub(lambda m, o=o: m.group(0) if m.group(0).startswith("'") else o, v) for v in out for o in options[:8]][:64]
    return out


def shell_base(command, root):
    """Where a command's relative paths resolve: the project root, or the directory a leading `cd` names."""
    m = re.match(r"\s*cd\s+(\S+)\s*(&&|;)", command)
    return resolve(m.group(1).strip("'\""), root) if m else root


ALONE = " Run the controller alone on its line, with nothing chained to it, and each write as its own command."


def controller_alone(command):
    """The controller alone on its line: the one hand that writes the run's files, held to its own rules. Chained, the
    hooks cannot tell its arguments from the shell's, so a compound command gets the ordinary checks. An operator inside
    quotes is text (a `--cmd '... ; echo'` does not chain, F21); a substitution inside double quotes still runs."""
    unsingled = re.sub(r"'[^']*'", "''", _no_heredoc_bodies(command))
    return (bool(re.search(r"gauntletctl\S*\s+\w", command)) and not re.search(r"&&|\|\||[;|<>]", _shell_text(command))
            and not re.search(r"`|\$\(", unsingled))


def scratch(real):
    """The harness's temp dir, where it tells every agent to keep temporary files ($TMPDIR and the session scratchpad
    under it; F24, F32). Never a path inside the project, so nothing a run judges or guards lives there, and no reader
    can open it."""
    return not inside(real, project()) and any(fnmatch.fnmatch(real, pat) or fnmatch.fnmatch(real + "/", pat)
                                               for pat in policy()["scratch_writes"])


def glob_base(pattern):
    """The literal directory prefix of a glob pattern."""
    keep = []
    for part in pattern.split("/"):
        if re.search(r"[*?\[{]", part):
            break
        keep.append(part)
    return "/".join(keep) or "."


def path_tokens(command, base=None):
    return [t for v in variants(command) for t in _path_tokens(v, base)]


def _path_tokens(command, base=None):
    """Tokens of a shell command that name a path: path-looking ones, and, given a base, a bare word that exists there
    (`cat heldout`). What a command writes is write_targets'. A string match, not a shell parser: Tier 2, never isolation."""
    try:
        lexer = shlex.shlex(_no_heredoc_bodies(command), posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        tokens = command.split()
    out = []
    for token in tokens:
        if "://" in token:  # a URL is not a path
            continue
        for part in re.split(r"[=:\s]", token):  # `a=b`, a revision path `HEAD:heldout/x`, a quoted "-- /path"
            if part and part not in SAFE and ("/" in part or part.startswith((".", "~")) or
                                               (base and os.path.lexists(os.path.join(base, part)))):
                out.append(part)
    return out


_ALL_OPERANDS = ("rm", "tee", "touch", "mkdir", "rmdir", "truncate", "chmod", "chown")
_LAST_OPERAND = ("mv", "cp", "ln", "install")
_GIT_WRITES = ("checkout", "restore", "rm", "mv", "apply", "stash", "clean", "reset", "clone")
_SEPARATORS = ("&&", "||", ";", "|", "&", "(", ")")


def write_targets(command, base):
    return [t for v in variants(command) for t in _write_targets(v, base)]


def _write_targets(command, base):
    """The paths a shell command writes: redirect targets, the operands of a write verb (the last one of a copy or a
    move), a `sed -i` file, `dd of=`, a git path. A sed script or a file that is only read is not one. A string match
    like the rest: Tier 2, never isolation. A caller denies a target it cannot resolve (see unresolved)."""
    try:
        lexer = shlex.shlex(_no_heredoc_bodies(command), posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        tokens = command.split()
    out, words, skip, heads, cwd = [], [], None, [0], [base]

    def add(*targets):  # resolved where the shell is at that point in the chain; one it cannot know stays as written
        out.extend(t if unresolved(t) else resolve(t, cwd[0]) for t in targets)

    def flush():
        if words and words[0] == "cd":
            args = [w for w in words[1:] if not w.startswith("-")]
            if args and not unresolved(args[0]):
                cwd[0] = resolve(args[0], cwd[0])  # a cd mid-chain moves where the next commands write
        elif words:
            verb, args = words[0], [w for w in words[1:] if not w.startswith("-")]
            if verb in _ALL_OPERANDS + _LAST_OPERAND + ("dd",) or (verb == "git" and args and args[0] in ("rm", "mv")):
                heads[0] += 1  # a write verb that heads its command; the hidden ones are counted below
            if verb in _ALL_OPERANDS:
                add(*args)
            elif verb in _LAST_OPERAND and ("-t" in words[:-1] or any(w.startswith("--target-directory=") for w in words)):
                if "-t" in words[:-1]:
                    add(words[words.index("-t") + 1])
                add(*(w.split("=", 1)[1] for w in words if w.startswith("--target-directory=")))
            elif verb in _LAST_OPERAND and args:
                add(args[-1])
            elif verb == "sed" and any(w.startswith("-i") or w.startswith("--in-place") for w in words[1:]):
                add(*_sed_files(words[1:]))
            elif verb == "dd":
                add(*(w[3:] for w in words[1:] if w.startswith("of=")))
            elif verb == "git" and args and args[0] in _GIT_WRITES:
                add(*(a for a in args[1:] if "://" not in a and ("/" in a or a.startswith("."))))
        words.clear()

    for token in tokens:
        if skip:  # the word after a redirect: a target after `>`, a source after `<`, a descriptor after `>&`
            if skip == ">" and token not in SAFE:
                add(token)
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
    # A write whose verb heads no command (`sudo rm`, `A=1 rm`, `xargs rm`, `find -delete`) could land on any path the
    # command names, so all of them are held to the rule. Quoted text and here-document bodies are not looked at.
    hidden = re.findall(r"(?<![\w./-])(rm|mv|cp|tee|touch|mkdir|rmdir|truncate|dd|ln|install|chmod|chown|-delete)(?![\w./-])",
                        _shell_text(command))
    if len(hidden) > heads[0]:
        out.extend(_path_tokens(command, base))
    # A substitution runs even inside double quotes: what it writes is written. Single-quoted text and a here-document's
    # body are only text: a JS template literal in a heredoc driver is not a command (F39)
    for inner in re.findall(r"\$\(([^()]*)\)|`([^`]*)`", re.sub(r"'[^']*'", "''", _no_heredoc_bodies(command))):
        out.extend(_write_targets(inner[0] or inner[1], base))
    return out


def _sed_files(words):
    """The files `sed -i` rewrites: its operands, less the script when no `-e` or `-f` gave it."""
    files, scripted, value = [], False, False
    for w in words:
        if value:
            value, scripted = False, True
        elif w in ("-e", "-f", "--expression", "--file"):
            value = True
        elif not w.startswith("-"):
            files.append(w)
    return files if scripted else files[1:]


_TEXT_ONLY = ("echo", "printf", "tr", "expr", "seq", "basename", "dirname", "true", "false", ":", "for", "case")
_PROGRAM_FIRST = ("grep", "egrep", "fgrep", "rg", "awk", "gawk", "mawk", "sed", "jq")  # their first operand is a program
_CODE = ("python", "python3", "node", "deno", "bun", "ruby", "perl")  # -c, -e: the next word is code
_SHELLS = ("sh", "bash", "zsh", "dash")
_KEYWORDS = ("do", "then", "else", "elif", "!", "time", "if", "while", "until", "{")
_LITERAL = re.compile(r"""(['"`])((?:/|\.\./|~)[^'"`\n]*)\1""")  # a quoted path in code or data


def read_targets(command, base):
    """The paths a shell command could open, by the shell's rules (F39): quotes gone, the variables it sets expanded
    (variants), each substitution judged as the command it runs and, where it stands as an operand, as a path nobody can
    resolve. Text, not paths: what echo or printf prints, the program grep, sed, awk or jq is given first, the code of
    `python -c` or `node -e`, and a here-document's data; in code and data a quoted path counts. What a command writes is
    write_targets'. Tier 2, never isolation: a matcher that knows a few commands, for a reader not trying to escape."""
    return [t for v in variants(command) for t in _read_targets(v, base)]


def _read_targets(command, base):
    bodies = [(bool(m.group(1)), m.group(3)) for m in re.finditer(
        r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n(.*?)(?:\n[ \t]*\2[ \t]*(?=\n|$)|$)", command, re.S)]
    shell, inner = _no_heredoc_bodies(command), []
    while True:  # innermost first; single-quoted text is only text, and `$((` is arithmetic
        blank = re.sub(r"'[^']*'", lambda m: "'" + " " * (len(m.group()) - 2) + "'", shell)
        m = re.search(r"\$\(([^()]*)\)|`([^`]*)`", blank)
        if not m:
            break
        g = 1 if m.group(1) is not None else 2
        inner.append(shell[m.start(g):m.end(g)])
        shell = shell[:m.start()] + "$SUBST" + shell[m.end():]
    out = [t for i in inner for t in _read_targets(i, base)]
    try:
        lexer = shlex.shlex(shell, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        tokens = shell.split()
    words, skip, owners, cwd = [], None, [], [base]

    def path(word):
        if re.search(r"\$[A-Za-z_{]|`", word):
            out.append(word)  # a variable it cannot know, or a substitution: the caller cannot say where it points
        elif "://" in word or word in SAFE or not ("/" in word or word.startswith((".", "~")) or
                                                    os.path.lexists(os.path.join(cwd[0], word))):
            return
        elif re.search(r"[*?\[]", word):
            base = glob_base(word)
            out.append(resolve("/" if word.startswith("/") and base == "." else base, cwd[0]))
        else:
            out.append(resolve(word, cwd[0]))

    def flush():
        w = list(words)
        words.clear()
        while w and (w[0] in _KEYWORDS or re.match(r"[A-Za-z_]\w*=", w[0])):
            w.pop(0)  # `do`, `then`, `A=1 cmd`
        if not w or os.path.basename(w[0]) in _TEXT_ONLY:
            return
        verb, args = os.path.basename(w[0]), w[1:]
        if verb == "cd":
            args = [a for a in args if not a.startswith("-")]
            path(args[0] if args else "~")
            if args and not re.search(r"\$[A-Za-z_{]|`", args[0]):
                cwd[0] = resolve(args[0], cwd[0])
            return
        scripted = verb in _PROGRAM_FIRST and any(a in ("-e", "-f", "--regexp", "--file", "--expression") or
                                                  a.startswith(("--regexp=", "--file=", "--expression=")) for a in args)
        program = verb in _PROGRAM_FIRST and not scripted
        value = None
        for a in args:
            if value:
                if value in ("-f", "--file"):
                    path(a)
                elif value == "code":
                    out.extend(resolve(lit, cwd[0]) for _, lit in _LITERAL.findall(a) if lit not in SAFE)
                value = None
            elif verb in _CODE and a in ("-c", "-e", "-p", "--eval", "--print"):
                value = "code"
            elif a in ("-e", "-f", "--regexp", "--file", "--expression") or (verb in _PROGRAM_FIRST and a in (
                    ("-F", "-v") if "awk" in verb else ("-A", "-B", "-C", "-m", "--max-count"))):
                value = a
            elif a.startswith("-"):
                if "=" in a and a.startswith(("--file=", "--input=")):
                    path(a.split("=", 1)[1])
            elif program:
                program = False  # the pattern, or the program
            else:
                path(a)

    for token in tokens:
        if skip:
            if skip == "<":
                path(token)
            elif skip == "<<":
                owners.append(os.path.basename(next((x for x in words if x not in _KEYWORDS), "")))
            skip = None
        elif token in _SEPARATORS:
            flush()
        elif token in (">", ">>", ">|", "&>", "&>>", "<", "<<", "<<-", "<<<", ">&", "<&"):
            if words and words[-1].isdigit():
                words.pop()
            skip = "<" if token == "<" else "<<" if token in ("<<", "<<-") else ">"
        else:
            words.append(token)
    flush()
    for owner, (delimiter_quoted, body) in zip(owners, bodies):
        if owner in _SHELLS:
            out.extend(_read_targets(body, cwd[0]))
        else:
            out.extend(resolve(lit, cwd[0]) for _, lit in _LITERAL.findall(body) if lit not in SAFE)
            if not delimiter_quoted:  # an unquoted delimiter: the shell runs the body's substitutions
                out.extend(t for i in re.findall(r"\$\(([^()]*)\)|`([^`]*)`", body) for t in _read_targets(i[0] or i[1], cwd[0]))
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

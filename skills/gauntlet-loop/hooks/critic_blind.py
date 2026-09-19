#!/usr/bin/env python3
"""PreToolUse, Read|Glob|Grep|Bash: a reader sees its pair and nothing else. Other agents pass through."""
import os
import re
import shlex

from _paths import allow, binding, deny, glob_base, inside, path_tokens, payload, project, resolve

ROLES = ("reader", "reader-alt")
FORBIDDEN = ("state.json", "events.jsonl", ".gauntlet/private", "reference/", "heldout/", "workbench", "CLAUDE.md")
REASON = "outside your working set"


def main():
    p = payload()
    if p.get("agent_type") not in ROLES:
        allow()
    root = project()
    pairs = os.path.join(root, ".gauntlet", "pairs")
    tool, ti, agent = p.get("tool_name"), p.get("tool_input", {}), p.get("agent_id")
    pair = binding(agent)
    home = os.path.join(pairs, pair) if pair else pairs

    if tool == "Bash":
        command = ti.get("command", "")
        if not pair:
            deny(REASON, "BLIND_BLOCK", p, command)
        for name in FORBIDDEN:
            if name in command:
                deny(REASON, "BLIND_BLOCK", p, command)
        # The body of a quoted heredoc is a script the shell expands nothing in: JS template literals are fine there.
        head, quoted, body = command.partition("<<'")
        for token in path_tokens(head):
            # `./$s/src` in a loop over a and b is fine; a path that starts with a variable, or hides a command, is not
            if token.startswith("$") or "$(" in token or "${" in token or "`" in token or not inside(resolve(token, home), home):
                deny(REASON, "BLIND_BLOCK", p, command)
        for literal in re.findall(r"""['"`\s(]((?:/|\.\./|~)[^'"`\s)]*)""", body) if quoted else []:
            if literal not in ("/dev/null",) and not inside(resolve(literal, home), home):
                deny(REASON, "BLIND_BLOCK", p, command)
        allow({**ti, "command": f"cd {shlex.quote(home)} && {command}"})

    target = ti.get("file_path") or ti.get("path") or "."
    if tool == "Glob":
        target = os.path.join(target, glob_base(ti.get("pattern", "")))
    real = resolve(target, root)
    if not inside(real, home) or real == pairs or any(name in real for name in FORBIDDEN):
        deny(REASON, "BLIND_BLOCK", p, target)
    if not pair:
        binding(agent, os.path.relpath(real, pairs).split(os.sep)[0])
    allow()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""PreToolUse, Read|Glob|Grep|Edit|Write|Bash: a builder or smoother stays inside its worktree and away from
held-out material, floors, migrations, infrastructure, deploys and secrets. Other agents pass through."""
import fnmatch
import os
import re

from _paths import (allow, binding, deny, glob_base, inside, path_tokens, payload, policy, project, resolve, shell_base,
                    tree_of, unresolved, write_targets)

ROLES = ("editor", "editor-fast")
B = policy()["builder_boundary"]
NO_READ, NO_WRITE_TREES, NO_WRITE_FILES, NO_COMMANDS = B["no_read"], B["no_write_trees"], B["no_write_files"], B["no_commands"]


def main():
    p = payload()
    if p.get("agent_type") not in ROLES:
        allow()
    root = project()
    wt = os.path.join(root, ".gauntlet", "wt")
    tool, ti, agent = p.get("tool_name"), p.get("tool_input", {}), p.get("agent_id")
    piece = binding(agent)
    home = os.path.join(wt, piece) if piece else wt

    def block(rule, what):
        deny(f"builder-boundary ({rule}): not yours to touch. Do not retry another way; return `BLOCKED: <reason>`.",
             "BOUNDARY_BLOCK", p, what)

    def check_read(real, what):
        if tree_of(real, NO_READ, root):
            block("held-out material", what)
        if inside(real, os.path.join(root, ".gauntlet")) and not inside(real, home):
            block("run state", what)

    def check_write(real, what):
        if not inside(real, home) or real == wt:
            block("outside your directory", what)
        inner = os.path.join(wt, os.path.relpath(real, wt).split(os.sep)[0])
        tree = tree_of(real, NO_WRITE_TREES, inner)
        if tree:
            block(tree, what)
        if any(fnmatch.fnmatch(os.path.basename(real), pat) for pat in NO_WRITE_FILES):
            block("secrets", what)

    if tool == "Bash":
        command = ti.get("command", "")
        for rule, pattern in NO_COMMANDS.items():
            if re.search(pattern, command):
                block(rule, command)
        base = shell_base(command, root)
        for token in path_tokens(command, base):
            check_read(resolve(token, base), command)
        for target in write_targets(command, base):
            if unresolved(target) or not inside(resolve(target, base), home):
                block("outside your directory", command)
        allow()

    target = ti.get("file_path") or ti.get("path") or "."
    if tool == "Glob":
        target = os.path.join(target, glob_base(ti.get("pattern", "")))
    real = resolve(target, root)
    if tool in ("Edit", "Write"):
        check_write(real, target)
        if not piece:
            binding(agent, os.path.relpath(real, wt).split(os.sep)[0])
    else:
        check_read(real, target)
    allow()


if __name__ == "__main__":
    main()

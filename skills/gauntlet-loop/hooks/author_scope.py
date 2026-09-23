#!/usr/bin/env python3
"""PreToolUse, Edit|Write|Bash: an author writes check files and frozen copies, nowhere else. Other agents pass through."""
import os

from _paths import allow, deny, inside, payload, policy, project, resolve, shell_base, unresolved, write_targets

TREES = policy()["floor_trees"] + policy()["author_scope"]["beyond_floor_trees"]


def main():
    p = payload()
    if p.get("agent_type") != "author":
        allow()
    root = project()
    ti = p.get("tool_input", {})
    mine = lambda real: any(inside(real, os.path.join(root, tree)) for tree in TREES)
    if p.get("tool_name") == "Bash":
        command = ti.get("command", "")
        base = shell_base(command, root)
        # ponytail: the shared string match, so a write through an interpreter or `curl -o` is not seen: Tier 2, never isolation
        if any(unresolved(t) or not mine(resolve(t, base)) for t in write_targets(command, base)):
            deny(f"author-scope: a shell command that writes names paths under {', '.join(TREES)} only. "
                 "Return the paths you have and stop.", "BOUNDARY_BLOCK", p, command)
        allow()
    target = ti.get("file_path", "")
    if not mine(resolve(target, root)):
        deny(f"author-scope: you write under {', '.join(TREES)} only. Return the paths you have and stop.",
             "BOUNDARY_BLOCK", p, target)
    allow()


if __name__ == "__main__":
    main()

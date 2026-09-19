#!/usr/bin/env python3
"""PreToolUse, Edit|Write: an author writes check files and frozen copies, nowhere else. Other agents pass through."""
import os

from _paths import allow, deny, inside, payload, project, resolve

TREES = ("tests/required", "heldout", "bench", "reference", ".gauntlet/staging")


def main():
    p = payload()
    if p.get("agent_type") != "author":
        allow()
    root = project()
    target = p.get("tool_input", {}).get("file_path", "")
    real = resolve(target, root)
    # ponytail: file tools only; an author's shell writes (a clone into reference/) are not path-checked here
    if not any(inside(real, os.path.join(root, tree)) for tree in TREES):
        deny(f"author-scope: you write under {', '.join(TREES)} only. Return the paths you have and stop.",
             "BOUNDARY_BLOCK", p, target)
    allow()


if __name__ == "__main__":
    main()

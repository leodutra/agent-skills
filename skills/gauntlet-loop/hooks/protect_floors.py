#!/usr/bin/env python3
"""PreToolUse, Edit|Write|Bash: tests, held-out sets, the reference and benchmarks are written by an author during
round zero and by nobody else, the lead included. Afterwards they change only through `gauntletctl floor`."""
import json
import os

from _paths import (ALONE, allow, controller_alone, deny, path_tokens, payload, policy, project, resolve, shell_base, tree_of,
                    unresolved, write_targets)

TREES = policy()["floor_trees"]


def round_zero(root):
    """True until the plan is committed, read from the controller's state cache; with no run, there is no round zero to end."""
    try:
        with open(os.path.join(root, ".gauntlet", "state.json")) as f:
            return not json.load(f)["run"]["plan_committed"]
    except (OSError, ValueError, KeyError, TypeError):
        return True


def main():
    p = payload()
    root = project()
    if p.get("agent_type") == "author" and round_zero(root):
        allow()
    ti = p.get("tool_input", {})
    if p.get("tool_name") == "Bash":
        command = ti.get("command", "")
        if controller_alone(command):
            allow()  # freeze, freeze-verify and `floor --to` write floor trees, under the controller's own rules
        base = shell_base(command, root)
        floor = lambda t: tree_of(resolve(t, base), TREES, root)
        targets = write_targets(command, base)
        hits = any(floor(t) for t in targets) or (any(unresolved(t) for t in targets) and any(floor(t) for t in path_tokens(command, base)))
        target = command if hits else None
    else:
        target = ti.get("file_path") if tree_of(resolve(ti.get("file_path", ""), root), TREES, root) else None
    if target:
        deny("protect-floors: tests, held-out sets, the reference and benchmarks are written by an author at round zero "
             "and change afterwards only through `gauntletctl floor add|amend --from <staged file>`. An author stages "
             "the file under .gauntlet/staging/; a builder returns `BLOCKED: <reason>`."
             + (ALONE if "gauntletctl" in (ti.get("command") or "") else ""), "BOUNDARY_BLOCK", p, target)
    allow()


if __name__ == "__main__":
    main()
